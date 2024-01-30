#include <cuda.h>
#include <cuda_runtime.h>
#include <cuda_runtime_api.h>
#include <iostream>
#include <iomanip>
#include <cassert>
#include <cmath>
#include <stdio.h>
#include <cublas_v2.h>
#include "helper_cuda.h"
#include "GPU_reduction.cuh"
// #include "ray_tracing_gpu.cuh"
#define DEBUG 0
#include "timer.h"

#define warpSize 32
#define INDEX_3D(N3, N2, N1, I3, I2, I1) (N1 * (N2 * I3 + I2) + I1)




__global__ void rt_gpu_python_results(float *d_result_list, float *d_python_result_list, size_t h_len_result)
{
	size_t id = blockDim.x * blockIdx.x + threadIdx.x;
	if (id < h_len_result)
	{
		float gpu_absorption = 0;
		for (size_t j = 0; j < len_coord_list; j++)
		{
			gpu_absorption += exp(-(d_result_list[id * len_coord_list * 2 + 2 * j + 0] + d_result_list[id * len_coord_list * 2 + 2 * j + 1]));
		}
		float gpu_absorption_mean = gpu_absorption / ((double)len_coord_list);
		d_python_result_list[id] = gpu_absorption_mean;
	}
}

__inline__ __device__ void transpose_device(float *input, int rows, int cols, float *output)
{
	for (int i = 0; i < rows; i++)
	{
		for (int j = 0; j < cols; j++)
		{
			output[j * rows + i] = input[i * cols + j];
		}
	}
}

__inline__ __device__ void dot_product_device(const float *A, const float *B, float *C, int m, int n, int p)
{
	//     In the provided example, the dimensions m, n, and p of the matrices are as follows:

	// Matrix A: m x n = 2 x 3 (2 rows, 3 columns)
	// Matrix B: n x p = 3 x 2 (3 rows, 2 columns)
	// Matrix C: m x p = 2 x 2 (2 rows, 2 columns)
	for (int i = 0; i < m; i++)
	{
		for (int j = 0; j < p; j++)
		{
			float sum = 0.0;
			for (int k = 0; k < n; k++)
			{
				sum += A[i * n + k] * B[k * p + j];
			}
			C[i * p + j] = sum;
		}
	}
}

__inline__ __device__ void kp_rotation_device(const float *axis, float theta, float *result)
{
	float x = axis[0];
	float y = axis[1];
	float z = axis[2];
	float c = cosf(theta);
	float s = sinf(theta);

	result[0] = c + (x * x) * (1 - c);
	result[1] = x * y * (1 - c) - z * s;
	result[2] = y * s + x * z * (1 - c);

	result[3] = z * s + x * y * (1 - c);
	result[4] = c + (y * y) * (1 - c);
	result[5] = -x * s + y * z * (1 - c);

	result[6] = -y * s + x * z * (1 - c);
	result[7] = x * s + y * z * (1 - c);
	result[8] = c + (z * z) * (1 - c);
}

__global__ void ray_tracing_rotation(const float *d_omega_axis, float *d_omega_list, float *d_kp_rotation_matrix, float *d_raw_xray, float *d_scattering_vector_list, float *d_rotated_xray_list, float *d_rotated_s1_list)
{
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	float rotation_matrix_frame_omega[9];
	float rotation_matrix_overall[9];
	float total_rotation_matrix[9];
	float rotated_xray[3];
	float rotated_s1[3];
	if (id < len_result)
	{
		kp_rotation_device(d_omega_axis, d_omega_list[id], rotation_matrix_frame_omega);
		dot_product_device((float *)rotation_matrix_frame_omega, d_kp_rotation_matrix, (float *)rotation_matrix_overall, 3, 3, 3);
		transpose_device((float *)rotation_matrix_overall, 3, 3, (float *)total_rotation_matrix);

		dot_product_device((float *)total_rotation_matrix, d_raw_xray, (float *)rotated_xray, 3, 3, 1);
		d_rotated_xray_list[3 * id] = rotated_xray[0];
		d_rotated_xray_list[3 * id + 1] = rotated_xray[1];
		d_rotated_xray_list[3 * id + 2] = rotated_xray[2];

		float scattering_vector[3] = {d_scattering_vector_list[id * 3],
									  d_scattering_vector_list[id * 3 + 1],
									  d_scattering_vector_list[id * 3 + 2]};
		dot_product_device((float *)total_rotation_matrix, (float *)scattering_vector, (float *)rotated_s1, 3, 3, 1);
		d_rotated_s1_list[3 * id] = rotated_s1[0];
		d_rotated_s1_list[3 * id + 1] = rotated_s1[1];
		d_rotated_s1_list[3 * id + 2] = rotated_s1[2];
	}
}

__inline__ __device__ int cube_face(int *ray_origin, float *ray_direction, int L1)
{
	float t_min = x_max * y_max * z_max, dtemp = 0;
	int face_id = 0;

	// float tx_min = (min_x - ray_origin[2]) / ray_direction[2];
	//  dtemp = (0 - ray_origin[2]) / ray_direction[2];
	if (L1)
	{
		dtemp = -(0 - ray_origin[2]) / ray_direction[2];
	}
	else
	{
		dtemp = (0 - ray_origin[2]) / ray_direction[2];
	}
	if (dtemp >= 0)
	{
		t_min = dtemp;
		face_id = 1;
	}

	// float tx_max = (max_x - ray_origin[2]) / ray_direction[2];
	if (L1)
	{
		dtemp = -(x_max - ray_origin[2]) / ray_direction[2];
	}
	else
	{
		dtemp = (x_max - ray_origin[2]) / ray_direction[2];
	}
	// dtemp = (x_max - ray_origin[2]) / ray_direction[2];
	if (dtemp >= 0 && dtemp < t_min)
	{
		t_min = dtemp;
		face_id = 2;
	}

	// float ty_min = (min_y - ray_origin[1]) / ray_direction[1];
	//  dtemp = (0 - ray_origin[1]) / ray_direction[1];
	if (L1)
	{
		dtemp = -(0 - ray_origin[1]) / ray_direction[1];
	}
	else
	{
		dtemp = (0 - ray_origin[1]) / ray_direction[1];
	}
	if (dtemp >= 0 && dtemp < t_min)
	{
		t_min = dtemp;
		face_id = 3;
	}

	// float ty_max = (max_y - ray_origin[1]) / ray_direction[1];
	//  dtemp = (y_max - ray_origin[1]) / ray_direction[1];
	if (L1)
	{
		dtemp = -(y_max - ray_origin[1]) / ray_direction[1];
	}
	else
	{
		dtemp = (y_max - ray_origin[1]) / ray_direction[1];
	}
	if (dtemp >= 0 && dtemp < t_min)
	{
		t_min = dtemp;
		face_id = 4;
	}
	// float tz_min = (min_z - ray_origin[0]) / ray_direction[0];
	//  dtemp = (0 - ray_origin[0]) / ray_direction[0];
	if (L1)
	{
		dtemp = -(0 - ray_origin[0]) / ray_direction[0];
	}
	else
	{
		dtemp = (0 - ray_origin[0]) / ray_direction[0];
	}
	if (dtemp >= 0 && dtemp < t_min)
	{
		t_min = dtemp;
		face_id = 5;
	}

	// float tz_max = (max_z - ray_origin[0]) / ray_direction[0];
	//  dtemp = (z_max - ray_origin[0]) / ray_direction[0];
	if (L1)
	{
		dtemp = -(z_max - ray_origin[0]) / ray_direction[0];
	}
	else
	{
		dtemp = (z_max - ray_origin[0]) / ray_direction[0];
	}
	if (dtemp >= 0 && dtemp < t_min)
	{
		t_min = dtemp;
		face_id = 6;
	}

	if (face_id == 1)
	{ // tx_min
		return 6;
	}
	else if (face_id == 2)
	{ // tx_max
		return 1;
	}
	else if (face_id == 3)
	{ // 3 ty_min
		return 4;
	}
	else if (face_id == 4)
	{ // 4 ty_max
		return 5;
	}
	else if (face_id == 5)
	{ // 5 tz_min
		return 2;
	}
	else if (face_id == 6)
	{ // 6 tz_max
		return 3;
	}
	else
	{
		return 0;
	}
}

__global__ void rt_gpu_get_face_overall(int *d_face, int *d_coord_list, float *d_rotated_s1_list, float *d_rotated_xray_list)
{
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	size_t batch_number = blockIdx.y * blockDim.y + threadIdx.y;
	int is_ray_incomming = id & 1;
	size_t pos = (id >> 1);
	// if (threadIdx.x==3){
	// printf("batch_number=%d, id=%ld, blockIdx.x=%d ,blockDim.x=%d, threadIdx.x=%d, blockIdx.y=%d, blockDim.y=%d, threadIdx.y=%d, is_ray_incomming=%d, pos=%d\n", batch_number, id, blockIdx.x, blockDim.x, threadIdx.x, blockIdx.y, blockDim.y, threadIdx.y, is_ray_incomming, pos);
	// }
	int coord[3];
	float ray_direction[3];
	// printf("batch number=%d, len_result=%d\n", batch_number, len_result);
	if (batch_number < len_result)
	{
		if (pos < len_coord_list)
		{
			coord[0] = d_coord_list[3 * pos + 0];
			coord[1] = d_coord_list[3 * pos + 1];
			coord[2] = d_coord_list[3 * pos + 2];

			if (is_ray_incomming == 1)
			{
				ray_direction[0] = d_rotated_xray_list[batch_number * 3 + 0];
				ray_direction[1] = d_rotated_xray_list[batch_number * 3 + 2];
				ray_direction[2] = d_rotated_xray_list[batch_number * 3 + 1];
			}
			else
			{
				ray_direction[0] = d_rotated_s1_list[batch_number * 3 + 0];
				ray_direction[1] = d_rotated_s1_list[batch_number * 3 + 2];
				ray_direction[2] = d_rotated_s1_list[batch_number * 3 + 1];
			}
			int face = cube_face(coord, ray_direction, is_ray_incomming);
			// printf("face=%d\n", face);

			d_face[batch_number * len_coord_list * 2 + id] = face;
		}
	}
}

__global__ void rt_gpu_get_face(int *d_face, int *d_coord_list, float *d_rotated_s1_list, float *d_rotated_xray_list, int batch_number)
{
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	int is_ray_incomming = id & 1;
	size_t pos = (id >> 1);

	int coord[3];
	float ray_direction[3];

	if (pos < len_coord_list)
	{
		coord[0] = d_coord_list[3 * pos + 0];
		coord[1] = d_coord_list[3 * pos + 1];
		coord[2] = d_coord_list[3 * pos + 2];

		if (is_ray_incomming == 1)
		{
			ray_direction[0] = d_rotated_xray_list[batch_number * 3 + 0];
			ray_direction[1] = d_rotated_xray_list[batch_number * 3 + 2];
			ray_direction[2] = d_rotated_xray_list[batch_number * 3 + 1];
		}
		else
		{
			ray_direction[0] = d_rotated_s1_list[batch_number * 3 + 0];
			ray_direction[1] = d_rotated_s1_list[batch_number * 3 + 2];
			ray_direction[2] = d_rotated_s1_list[batch_number * 3 + 1];
		}
		int face = cube_face(coord, ray_direction, is_ray_incomming);
		d_face[id] = face;
	}
}

__inline__ __device__ void get_theta_phi(float *theta, float *phi, float *ray_direction, int L1)
{
	if (L1 == 1)
	{
		ray_direction[0] = -ray_direction[0];
		ray_direction[1] = -ray_direction[1];
		ray_direction[2] = -ray_direction[2];
	}

	if (ray_direction[1] == 0)
	{
		(*theta) = atanf(-ray_direction[2] / (-sqrtf(ray_direction[0] * ray_direction[0] + ray_direction[1] * ray_direction[1]) + 0.001));
		(*phi) = atanf(-ray_direction[0] / (ray_direction[1] + 0.001));
	}
	else
	{
		if (ray_direction[1] < 0)
		{
			(*theta) = atanf(-ray_direction[2] / sqrtf(ray_direction[0] * ray_direction[0] + ray_direction[1] * ray_direction[1]));
			(*phi) = atanf(-ray_direction[0] / (ray_direction[1]));
		}
		else
		{
			if (ray_direction[2] < 0)
			{
				(*theta) = M_PI - atanf(-ray_direction[2] / sqrtf(ray_direction[0] * ray_direction[0] + ray_direction[1] * ray_direction[1]));
			}
			else
			{
				(*theta) = -M_PI - atanf(-ray_direction[2] / sqrtf(ray_direction[0] * ray_direction[0] + ray_direction[1] * ray_direction[1]));
			}
			(*phi) = -atanf(-ray_direction[0] / (-ray_direction[1]));
		}
	}
}

__global__ void rt_gpu_angles(float *d_angles, float *d_rotated_s1_list, float *d_rotated_xray_list, int nBatches, int batch_number)
{
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	size_t batch = (id >> 1);
	int is_ray_incomming = id & 1;

	float theta = 0, phi = 0;
	float ray_direction[3];

	if (batch < nBatches)
	{
		if (is_ray_incomming == 1)
		{
			ray_direction[0] = d_rotated_xray_list[batch_number * 3 + 0];
			ray_direction[1] = d_rotated_xray_list[batch_number * 3 + 1];
			ray_direction[2] = d_rotated_xray_list[batch_number * 3 + 2];
		}
		else
		{
			ray_direction[0] = d_rotated_s1_list[batch_number * 3 + 0];
			ray_direction[1] = d_rotated_s1_list[batch_number * 3 + 1];
			ray_direction[2] = d_rotated_s1_list[batch_number * 3 + 2];
		}

		get_theta_phi(&theta, &phi, ray_direction, is_ray_incomming);

		// printf("pos=[%d; %d] theta=%f; phi=%f;\n", (int) (2*id + 0), (int) (2*id + 1), theta, phi);

		d_angles[2 * id + 0] = theta;
		d_angles[2 * id + 1] = phi;
	}
	// printf("d_angles =[%f,%f,%f,%f]  ", d_angles[0], d_angles[1], d_angles[2], d_angles[3]);
}

__global__ void rt_gpu_angles_overall(float *d_angles, float *d_rotated_s1_list, float *d_rotated_xray_list)
{
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	size_t batch = (id >> 1);
	int is_ray_incomming = id & 1;

	float theta = 0, phi = 0;
	float ray_direction[3];
	// if ( blockIdx.x==1500){
	// 	printf("id=%d, theta=%f, phi=%f\n", id, theta, phi);
	// 	printf("ray_direction=[%f, %f, %f]\n", ray_direction[0], ray_direction[1], ray_direction[2]);
	// }
	if (batch < len_result)
	{
		if (is_ray_incomming == 1)
		{
			ray_direction[0] = d_rotated_xray_list[batch * 3 + 0];
			ray_direction[1] = d_rotated_xray_list[batch * 3 + 1];
			ray_direction[2] = d_rotated_xray_list[batch * 3 + 2];
		}
		else
		{
			ray_direction[0] = d_rotated_s1_list[batch * 3 + 0];
			ray_direction[1] = d_rotated_s1_list[batch * 3 + 1];
			ray_direction[2] = d_rotated_s1_list[batch * 3 + 2];
		}

		get_theta_phi(&theta, &phi, ray_direction, is_ray_incomming);

		// printf("pos=[%d; %d] theta=%f; phi=%f;\n", (int) (2*id + 0), (int) (2*id + 1), theta, phi);

		d_angles[2 * id + 0] = theta;
		d_angles[2 * id + 1] = phi;
	}
	// printf("d_angles =[%f,%f,%f,%f]  ", d_angles[0], d_angles[1], d_angles[2], d_angles[3]);
}

__inline__ __device__ void get_increment_ratio(
	float *increment_ratio_x,
	float *increment_ratio_y,
	float *increment_ratio_z,
	float theta,
	float phi,
	int face)
{
	if (face == 1)
	{
		*increment_ratio_x = -1;
		*increment_ratio_y = tanf(M_PI - theta) / cosf(fabs(phi));
		*increment_ratio_z = tanf(phi);
	}
	else if (face == 2)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*increment_ratio_x = 1 / tanf(fabs(phi));
			*increment_ratio_y = tanf(theta) / sinf(fabs(phi));
			*increment_ratio_z = -1;
		}
		else
		{
			*increment_ratio_x = 1 / tanf(fabs(phi));
			*increment_ratio_y = tanf(M_PI - theta) / sinf(fabs(phi));
			*increment_ratio_z = -1;
		}
	}
	else if (face == 3)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*increment_ratio_x = 1 / tanf(fabs(phi));
			*increment_ratio_y = tanf(theta) / sinf(fabs(phi));
			*increment_ratio_z = 1;
		}
		else
		{
			*increment_ratio_x = 1 / (tanf(fabs(phi)));
			*increment_ratio_y = tanf(M_PI - theta) / sinf(fabs(phi));
			*increment_ratio_z = 1;
		}
	}
	else if (face == 4)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*increment_ratio_x = cosf(fabs(phi)) / tanf(fabs(theta));
			*increment_ratio_y = 1;
			*increment_ratio_z = sinf(phi) / tanf(fabs(theta));
		}
		else
		{
			*increment_ratio_x = cosf(fabs(phi)) / (tanf((M_PI - fabs(theta))));
			*increment_ratio_y = 1;
			*increment_ratio_z = sinf(-phi) / (tanf((M_PI - fabs(theta))));
		}
	}
	else if (face == 5)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*increment_ratio_x = cosf(fabs(phi)) / (tanf(fabs(theta)));
			*increment_ratio_y = -1;
			*increment_ratio_z = sinf(phi) / (tanf(fabs(theta)));
		}
		else
		{
			*increment_ratio_x = cosf(fabs(phi)) / (tanf(M_PI - fabs(theta)));
			*increment_ratio_y = -1;
			*increment_ratio_z = sinf(phi) / (tanf(M_PI - fabs(theta)));
		}
	}
	else if (face == 6)
	{
		*increment_ratio_x = -1;
		*increment_ratio_y = tanf(theta) / cosf(phi);
		*increment_ratio_z = tanf(phi);
	}
}

__global__ void rt_gpu_increments_overall(float *d_increments, float *d_angles)
{
	// store increments according to different faces and different thetas
	// and for one single reflection, the increments are the same
	// so we only need to store the increments for one single reflection with
	// different crystal voxel positions
	// size_t id = threadIdx.x;
	size_t id = threadIdx.x;
	size_t batch = blockIdx.x;
	int face = id % 6;
	int is_ray_incomming = id / 6.0f;
	if (batch < len_result)
	{

		float theta = 0, phi = 0;
		if (is_ray_incomming == 1)
		{
			theta = d_angles[4 * batch + 2 + 0];
			phi = d_angles[4 * batch + 2 + 1];
		}
		else
		{
			theta = d_angles[4 * batch + 0];
			phi = d_angles[4 * batch + 1];
		}

		float ix = 0, iy = 0, iz = 0;
		get_increment_ratio(&ix, &iy, &iz, theta, phi, face + 1);

		d_increments[36 * batch + 3 * threadIdx.x + 0] = ix;
		d_increments[36 * batch + 3 * threadIdx.x + 1] = iy;
		d_increments[36 * batch + 3 * threadIdx.x + 2] = iz;
	}
}

__global__ void rt_gpu_increments(float *d_increments, float *d_angles)
{
	// store increments according to different faces and different thetas
	// and for one single reflection, the increments are the same
	// so we only need to store the increments for one single reflection with
	// different crystal voxel positions
	size_t id = threadIdx.x;
	size_t batch = blockIdx.x;
	int face = id % 6;
	int is_ray_incomming = id / 6.0f;

	float theta = 0, phi = 0;
	if (is_ray_incomming == 1)
	{
		theta = d_angles[4 * batch + 2 + 0];
		phi = d_angles[4 * batch + 2 + 1];
	}
	else
	{
		theta = d_angles[4 * batch + 0];
		phi = d_angles[4 * batch + 1];
	}

	float ix = 0, iy = 0, iz = 0;
	get_increment_ratio(&ix, &iy, &iz, theta, phi, face + 1);

	d_increments[36 * batch + 3 * threadIdx.x + 0] = ix;
	d_increments[36 * batch + 3 * threadIdx.x + 1] = iy;
	d_increments[36 * batch + 3 * threadIdx.x + 2] = iz;
}

__inline__ __device__ void get_new_coordinates(
	int *new_x, int *new_y, int *new_z,
	int x, int y, int z,
	float increment_ratio_x, float increment_ratio_y, float increment_ratio_z,
	int increment, float theta, int face)
{
	if (face == 1)
	{
		if (theta > 0)
		{
			// this -1 represents that the opposition of direction
			// between the lab x-axis and the wavevector
			*new_x = (int)(x - increment * increment_ratio_x);
			*new_y = (int)(y - increment * increment_ratio_y);
			*new_z = (int)(z - increment * increment_ratio_z);
		}
		else
		{
			// this -1 represents that the opposition of direction
			// between the lab x-axis and the wavevector
			*new_x = (int)(x - increment * increment_ratio_x + 0.5);
			*new_y = (int)(y - increment * increment_ratio_y + 0.5);
			*new_z = (int)(z - increment * increment_ratio_z + 0.5);
		}
	}
	else if (face == 2)
	{
		if (fabs(theta) < M_PI / 2)
		{
			if (theta > 0)
			{
				*new_x = (int)(x + -1 * increment * increment_ratio_x);
				*new_y = (int)(y - increment * increment_ratio_y);
				*new_z = (int)(z + increment * increment_ratio_z);
			}
			else
			{
				*new_x = (int)(x + -1 * increment * increment_ratio_x + 0.5);
				*new_y = (int)(y - increment * increment_ratio_y + 0.5);
				*new_z = (int)(z + increment * increment_ratio_z + 0.5);
			}
		}
		else
		{
			if (theta > 0)
			{
				*new_x = (int)(x + 1 * increment * increment_ratio_x);
				*new_y = (int)(y - increment * increment_ratio_y);
				*new_z = (int)(z + increment * increment_ratio_z);
			}
			else
			{
				*new_x = (int)(x + 1 * increment * increment_ratio_x + 0.5);
				*new_y = (int)(y - increment * increment_ratio_y + 0.5);
				*new_z = (int)(z + increment * increment_ratio_z + 0.5);
			}
		}
	}
	else if (face == 3)
	{
		if (fabs(theta) < M_PI / 2)
		{
			if (theta > 0)
			{
				*new_x = (int)(x + -1 * increment * increment_ratio_x);
				*new_y = (int)(y - increment * increment_ratio_y);
				*new_z = (int)(z + increment * increment_ratio_z);
			}
			else
			{
				*new_x = (int)(x + -1 * increment * increment_ratio_x + 0.5);
				*new_y = (int)(y - increment * increment_ratio_y + 0.5);
				*new_z = (int)(z + increment * increment_ratio_z + 0.5);
			}
		}
		else
		{
			if (theta > 0)
			{
				*new_x = (int)(x + 1 * increment * increment_ratio_x);
				*new_y = (int)(y - increment * increment_ratio_y);
				*new_z = (int)(z + increment * 1);
			}
			else
			{
				*new_x = (int)(x + 1 * increment * increment_ratio_x + 0.5);
				*new_y = (int)(y - increment * increment_ratio_y + 0.5);
				*new_z = (int)(z + increment * 1 + 0.5);
			}
		}
	}
	else if (face == 4)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*new_x = (int)(x + -1 * increment * increment_ratio_x);
			*new_y = (int)(y - increment * increment_ratio_y);
			*new_z = (int)(z + increment * increment_ratio_z);
		}
		else
		{
			*new_x = (int)(x + 1 * increment * increment_ratio_x);
			*new_y = (int)(y - increment * increment_ratio_y);
			*new_z = (int)(z + increment * increment_ratio_z);
		}
	}
	else if (face == 5)
	{
		if (fabs(theta) < M_PI / 2)
		{
			*new_x = (int)(x + -1 * increment * increment_ratio_x + 0.5);
			*new_y = (int)(y - increment * increment_ratio_y + 0.5);
			*new_z = (int)(z + increment * increment_ratio_z + 0.5);
		}
		else
		{
			*new_x = (int)(x + 1 * increment * increment_ratio_x + 0.5);
			*new_y = (int)(y - increment * increment_ratio_y + 0.5);
			*new_z = (int)(z - increment * increment_ratio_z + 0.5);
		}
	}
	else if (face == 6)
	{
		if (theta > 0)
		{
			*new_x = (int)(x + increment * increment_ratio_x);
			*new_y = (int)(y - increment * increment_ratio_y);
			*new_z = (int)(z + increment * increment_ratio_z);
		}
		else
		{
			*new_x = (int)(x + increment * increment_ratio_x + 0.5);
			*new_y = (int)(y - increment * increment_ratio_y + 0.5);
			*new_z = (int)(z + increment * increment_ratio_z + 0.5);
		}
	}
}

__inline__ __device__ void get_distance_2(float *total_length, float s_sum, float increment_ratio_x, float increment_ratio_y, float increment_ratio_z, int face)
{
	float dist_x, dist_y, dist_z;
	if (face == 1)
	{
		dist_x = (s_sum - 1.0f);
		dist_y = (s_sum - 1.0f) * increment_ratio_y;
		dist_z = (s_sum - 1.0f) * increment_ratio_z;
	}
	else if (face == 2)
	{
		dist_x = (s_sum - 1.0f) * increment_ratio_x;
		dist_y = (s_sum - 1.0f) * increment_ratio_y;
		dist_z = (s_sum - 1.0f);
	}
	else if (face == 3)
	{
		dist_x = (s_sum - 1.0f) * increment_ratio_x;
		dist_y = (s_sum - 1.0f) * increment_ratio_y;
		dist_z = (s_sum - 1.0f);
	}
	else if (face == 4)
	{
		dist_x = (s_sum - 1.0f) * increment_ratio_x;
		dist_y = (s_sum - 1.0f);
		dist_z = (s_sum - 1.0f) * increment_ratio_z;
	}
	else if (face == 5)
	{
		dist_x = (s_sum - 1.0f) * increment_ratio_x;
		dist_y = (s_sum - 1.0f);
		dist_z = (s_sum - 1.0f) * increment_ratio_z;
	}
	else if (face == 6)
	{
		dist_x = (s_sum - 1.0f);
		dist_y = (s_sum - 1.0f) * increment_ratio_y;
		dist_z = (s_sum - 1.0f) * increment_ratio_z;
	}
	// 	if (face == 1)
	// {
	// 	dist_x = (s_sum  );
	// 	dist_y = (s_sum  ) * increment_ratio_y;
	// 	dist_z = (s_sum  ) * increment_ratio_z;
	// }
	// else if (face == 2)
	// {
	// 	dist_x = (s_sum  ) * increment_ratio_x;
	// 	dist_y = (s_sum  ) * increment_ratio_y;
	// 	dist_z = (s_sum  );
	// }
	// else if (face == 3)
	// {
	// 	dist_x = (s_sum  ) * increment_ratio_x;
	// 	dist_y = (s_sum  ) * increment_ratio_y;
	// 	dist_z = (s_sum  );
	// }
	// else if (face == 4)
	// {
	// 	dist_x = (s_sum  ) * increment_ratio_x;
	// 	dist_y = (s_sum  );
	// 	dist_z = (s_sum  ) * increment_ratio_z;
	// }
	// else if (face == 5)
	// {
	// 	dist_x = (s_sum  ) * increment_ratio_x;
	// 	dist_y = (s_sum  );
	// 	dist_z = (s_sum  ) * increment_ratio_z;
	// }
	// else if (face == 6)
	// {
	// 	dist_x = (s_sum  );
	// 	dist_y = (s_sum  ) * increment_ratio_y;
	// 	dist_z = (s_sum  ) * increment_ratio_z;
	// }
	else
	{
		dist_x = 0;
		dist_y = 0;
		dist_z = 0;
	}
	// if (id <2){
	// printf("id: %d dist_x: %f, dist_y: %f, dist_z: %f\n",id, dist_x, dist_y, dist_z);
	// }
	*total_length = sqrtf(
		(dist_x * voxel_length_x) * (dist_x * voxel_length_x) +
		(dist_y * voxel_length_y) * (dist_y * voxel_length_y) +
		(dist_z * voxel_length_z) * (dist_z * voxel_length_z));
}

__global__ void rt_gpu_absorption(int8_t *d_label_list, int *d_coord_list, int *d_face, float *d_angles, float *d_increments, float *d_result_list, size_t index)
{
	size_t id = blockIdx.x;
	int is_ray_incomming = id & 1;
	size_t pos = (id >> 1); /* the right shift operation effectively divided the value of id by 2 (since shifting the bits to the right by 1 is equivalent to integer division by 2).*/
	float increments[3];
	int face = 0;
	int coord[3];
	float theta, phi;
	__shared__ float s_absorption[512];
	// __shared__ int s_ray_classes[512];
	int cr_l_2_int = 0;
	int li_l_2_int = 0;
	int bu_l_2_int = 0;
	int lo_l_2_int = 0;

	// Load coordinates
	coord[0] = d_coord_list[3 * pos + 0]; // z
	coord[1] = d_coord_list[3 * pos + 1]; // y
	coord[2] = d_coord_list[3 * pos + 2]; // x

	// Load face
	// face = d_face[index * len_coord_list * 2 + id];
	face = d_face[id];
	// printf("index= %ld face=%d\n", index*len_coord_list*2 + id,face);

	// Load angle
	// theta = d_angles[4 * blockIdx.y + 2 * is_ray_incomming];
	theta = d_angles[4 * index + 2 * is_ray_incomming];
	// phi = d_angles[4*blockIdx.y + 2*is_ray_incomming + 1];

	// Load Increment
	// size_t incr_pos = 36 * blockIdx.y + 18 * is_ray_incomming + 3 * (face - 1);
	size_t incr_pos = 36 * index + 18 * is_ray_incomming + 3 * (face - 1);
	// get_increment_ratio(&increments[0], &increments[1], &increments[2], theta, phi, face);
	increments[0] = d_increments[incr_pos + 0];
	increments[1] = d_increments[incr_pos + 1];
	increments[2] = d_increments[incr_pos + 2];

	// Calculate number of iterations of blocks
	// trick for ceiling
	int nIter = (int)((diagonal + blockDim.x - 1) / blockDim.x);

	// if (index==213427){
	// 	printf("index= %ld face=%d\n", index*len_coord_list*2 + id,face);
	// 	printf("index= %ld face=%d\n", index*len_coord_list*2 + id,face);
	// }

	for (int f = 0; f < nIter; f++)
	{
		// calculate position based on threads id
		// check if the position is within a cube_face
		// write into ray_direction
		int lpos = (f * blockDim.x + threadIdx.x);
		int x, y, z;
		get_new_coordinates(
			&x, &y, &z,
			coord[2], coord[1], coord[0],
			increments[0], increments[1], increments[2],
			lpos, theta, face);
		int label = 0;

		if (
			x < x_max && y < y_max && z < z_max &&
			x >= 0 && y >= 0 && z >= 0)
		{
			size_t cube_pos = INDEX_3D(
				z_max, y_max, x_max,
				z, y, x);
			label = (int)d_label_list[cube_pos];

			if (label == 3)
				cr_l_2_int++;
			else if (label == 1)
				li_l_2_int++;
			else if (label == 2)
				lo_l_2_int++;
			else if (label == 4)
				bu_l_2_int++;
			else
			{
			}
		}
		// if (lpos < diagonal)
		// {
		// 	size_t gpos = blockIdx.x * diagonal + lpos;
		// 	d_ray_classes[gpos] = label;
		// }
	}

	float total_length;
	get_distance_2(&total_length, diagonal, increments[0], increments[1], increments[2], face);

	float cr_l = (total_length * cr_l_2_int) / ((float)diagonal);
	float li_l = (total_length * li_l_2_int) / ((float)diagonal);
	float lo_l = (total_length * lo_l_2_int) / ((float)diagonal);
	float bu_l = (total_length * bu_l_2_int) / ((float)diagonal);

	float absorption = 0;
	float li_absorption = 0;
	float lo_absorption = 0;
	float cr_absorption = 0;
	float bu_absorption = 0;
	s_absorption[threadIdx.x] = coeff_li * li_l + coeff_lo * lo_l + coeff_cr * cr_l + coeff_bu * bu_l;

	__syncthreads();
	absorption = Reduce_SM(s_absorption);

	Reduce_WARP(&absorption);

	__syncthreads();

	// calculation of the absorption for given ray
	if (threadIdx.x == 0)
	{
		// d_absorption[id] = absorption;
		d_result_list[index * len_coord_list * 2 + id] = absorption;
	}
}

__device__ void determine_boundaries_v2(int *s_ray_classes, int offset, int *boundaries, int *class_values, int *boundary_count)
{
	int tid = threadIdx.x % warpSize; // Thread id within the warp

	int val = s_ray_classes[offset + tid];
	int prev_val;

	if (tid == 0)
	{
		prev_val = (threadIdx.x > 0) ? s_ray_classes[offset + tid - 1] : 3; // Fetch directly from shared memory
	}
	else
	{
		prev_val = __shfl_down_sync(0xFFFFFFFF, val, 1); // Get the value of the previous thread in the warp
	}

	if (threadIdx.x != 0 && val != prev_val)
	{

		int local_count = atomicAdd(boundary_count, 1);
		boundaries[local_count] = offset + tid + 1;
		class_values[local_count] = val;
	}
}

// __device__ inline void determine_boundaries_v3( int offset, int *boundaries, int *class_values, int *boundary_count, int coord_2, int coord_1, int coord_0, float increments_0, float increments_1, float increments_2,  float theta, int face, int8_t*d_label_list)
// {
// 	int lpos = (blockIdx.x * blockDim.x + threadIdx.x);
// 	int warpId = lpos / warpSize;
// 	int laneId = lpos % warpSize;
// 	int x, y, z;
// 	int prev_val;
// 	get_new_coordinates(
// 		&x, &y, &z,
// 		coord_2, coord_1, coord_0,
// 		increments_0, increments_1, increments_2,
// 		lpos, theta, face);
// 	int label = 0;
// 	if (
// 		x < x_max && y < y_max && z < z_max &&
// 		x >= 0 && y >= 0 && z >= 0)
// 	{
// 		size_t cube_pos = INDEX_3D(
// 			z_max, y_max, x_max,
// 			z, y, x);
// 	}
// 	if (laneId == 0 && warpId==0){

// 	}
// 	else{
// 		prev_val = __shfl_down_sync(0xFFFFFFFF, label, 1);
// 		if (threadIdx.x != 0 && label != prev_val)
// 		{

// 			int local_count = atomicAdd(boundary_count, 1);
// 			boundaries[local_count] = lpos;
// 			class_values[local_count] = label;
// 		}
// 	}
//     int tid = threadIdx.x;
//     int laneId = tid % 32; // Warp lane ID

//     int val = s_ray_classes[tid];
//     int prev_val = (laneId > 0) ? __shfl_sync(0xFFFFFFFF, val, laneId - 1) : (tid > 0) ? s_ray_classes[tid - 1] : -1;

//     // Check if there's a boundary at this thread
//     bool isBoundary = (val != prev_val);

//     // Use warp-level primitives to compactly store boundaries
//     unsigned mask = __ballot_sync(0xFFFFFFFF, isBoundary);

//     if (mask != 0 && laneId == 0) // Only the first thread in the warp handles the atomic operation
//     {
//         int local_count = atomicAdd(&boundary_count, __popc(mask)); // Add the number of set bits in mask
//         for (int i = 0; i < 32; i++)
//         {
//             if ((mask & (1 << i)) != 0) // Check each bit in the mask
//             {
//                 boundaries[local_count] = tid - laneId + i;
//                 class_values[local_count] = s_ray_classes[tid - laneId + i];
//                 local_count++;
//             }
//         }
//     }
// }

__device__ void determine_boundaries_nowarp(int *s_ray_classes, int *boundaries, int *class_values, int *boundary_count, int len_ray_classes, size_t lpos)
{

	int val = s_ray_classes[lpos];
	int prev_val;

	if (lpos == 0)
	{
		prev_val = 3; // Fetch directly from shared memory
	}
	else
	{
		// prev_val = __shfl_down_sync(0xFFFFFFFF, val, 1); // Get the value of the
		prev_val = s_ray_classes[lpos - 1];
		if (val != prev_val)
		{
			int local_count = atomicAdd(boundary_count, 1);
			// int diff = val-prev_val;
			boundaries[local_count] = lpos; // writing to the boundaries takes the most of the time
			class_values[lpos] = val;
		}
	}
}

__device__ void determine_boundaries(int *s_ray_classes, int offset, int *boundaries, int *class_values, int *boundary_count)
{
	int tid = threadIdx.x % warpSize; // Thread id within the warp
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	int val = s_ray_classes[offset + tid];
	int prev_val;

	if (tid == 0)
	{
		prev_val = (threadIdx.x > 0) ? s_ray_classes[offset + tid - 1] : 3; // Fetch directly from shared memory
	}
	else
	{
		prev_val = __shfl_down_sync(0xFFFFFFFF, val, 1); // Get the value of the previous thread in the warp
	}

	if (threadIdx.x != 0 && val != prev_val)
	{

		int local_count = atomicAdd(boundary_count, 1);
		boundaries[local_count] = offset + tid + 1;
		class_values[local_count] = val;
	}
}

// __device__ void determine_boundaries(int *s_ray_classes, int offset, int *boundaries, int *class_values, int *boundary_count,int8_t* d_label_list, int coord[3],float increments[3],size_t lpos, float theta, int face)
// {
// 	int tid = threadIdx.x % warpSize; // Thread id within the warp
// 	int x, y, z;
// 	get_new_coordinates(
// 			&x, &y, &z,
// 			coord[2], coord[1], coord[0],
// 			increments[0], increments[1], increments[2],
// 			lpos, theta, face);
// 	int label = 0;
// 	if (
// 			x < x_max && y < y_max && z < z_max &&
// 			x >= 0 && y >= 0 && z >= 0)
// 		{
// 			size_t cube_pos = INDEX_3D(
// 				z_max, y_max, x_max,
// 				z, y, x);
// 			label = (int)d_label_list[cube_pos];

// 		}
// 	// int val = s_ray_classes[offset + tid];
// 	int val =label;
// 	int prev_val;

// 	if (tid == 0)
// 	{
// 		if (offset==0){

// 		}
// 		else{
// 		prev_val = (threadIdx.x > 0) ? s_ray_classes[offset + tid - 1] : 3; }// Fetch directly from shared memory
// 	}
// 	else
// 	{
// 		prev_val = __shfl_down_sync(0xFFFFFFFF, val, 1); // Get the value of the previous thread in the warp
// 	}

// 	if (threadIdx.x != 0 && val != prev_val)
// 	{

// 		int local_count = atomicAdd(boundary_count, 1);
// 		boundaries[local_count] = offset + tid + 1;
// 		class_values[local_count] = val;
// 	}
// }

__device__ void calculate_distances(int *boundaries, int *class_values, int count, int *distances)
{
	for (int i = 0; i < count - 1; i++)
	{
		distances[i] = boundaries[i + 1] - boundaries[i];
	}
	distances[count - 1] = warpSize - boundaries[count - 1];
}

__global__ void rt_gpu_absorption_shuffle_v2(int8_t *d_label_list, int *d_coord_list, int *d_face, float *d_angles, float *d_increments, float *d_result_list, size_t index)
{
	size_t id = blockIdx.x;
	int is_ray_incomming = id & 1;
	size_t pos = (id >> 1); /* the right shift operation effectively divided the value of id by 2 (since shifting the bits to the right by 1 is equivalent to integer division by 2).*/
	// float increments[3];
	int face = 0;
	// int coord[3];
	float theta, phi;
	// __shared__ float s_absorption[1024];
	// extern __shared__ int s_ray_classes[];
	// extern __shared__ int DynamicsharedMemory[];
	// int * s_ray_classes = DynamicsharedMemory;
	// int * boundaries = &DynamicsharedMemory[diagonal];
	// int * class_values = &DynamicsharedMemory[diagonal*2];

	// extern __shared__ int s_ray_classes[];
	int len_ray_classes = 2048;
	__shared__ int s_ray_classes[2048];

	__shared__ int boundaries[128];
	__shared__ int class_values[128];
	float increments_0, increments_1, increments_2;
	int coord_0, coord_1, coord_2;
	// int ray_classes[2048];

	__shared__ int boundary_count;
	__shared__ int pre_warp_last;
	// __shared__ float cr_l;
	// __shared__ float li_l;
	// __shared__ float bu_l;
	// __shared__ float lo_l;
	int cr_l = 0;
	int li_l = 0;
	int bu_l = 0;
	int lo_l = 0;
	int total_length;
	float absorption;

	if (threadIdx.x == 0)
	{
		boundary_count = 0;
		// cr_l = 0;
		// li_l = 0;
		// bu_l = 0;
		// lo_l = 0;
	}
	// extern __shared__ float s_absorption[];

	// Load coordinates
	coord_0 = d_coord_list[3 * pos + 0]; // z
	coord_1 = d_coord_list[3 * pos + 1]; // y
	coord_2 = d_coord_list[3 * pos + 2]; // x

	// Load face
	// face = d_face[index * len_coord_list * 2 + id];  // outside  for loop
	face = d_face[id]; // within  for loop

	// printf("index= %ld face=%d\n", index*len_coord_list*2 + id,face);

	// Load angle
	theta = d_angles[4 * index + 2 * is_ray_incomming]; // outside for loop
	// theta = d_angles[4 * blockIdx.y + 2 * is_ray_incomming]; // within for loop
	// phi = d_angles[4*blockIdx.y + 2*is_ray_incomming + 1];

	// Load Increment
	size_t incr_pos = 36 * index + 18 * is_ray_incomming + 3 * (face - 1); // outside for loop
	// size_t incr_pos = 36 * blockIdx.y + 18 * is_ray_incomming + 3 * (face - 1); //within for loop

	// get_increment_ratio(&increments[0], &increments[1], &increments[2], theta, phi, face);
	increments_0 = d_increments[incr_pos + 0];
	increments_1 = d_increments[incr_pos + 1];
	increments_2 = d_increments[incr_pos + 2];

	// Calculate number of iterations of blocks
	// trick for ceiling

	// int nIter = (int)((diagonal + blockDim.x - 1) / blockDim.x);

	// for (int f = 0; f < nIter; f++)
	// {
	// 	int lpos = (f * blockDim.x + threadIdx.x);
	// determine_boundaries_v3( lpos,warpId * warpSize, boundaries, class_values, &boundary_count);
	// }
	int nIter = (int)((diagonal + blockDim.x - 1) / blockDim.x);

	for (int f = 0; f < nIter; f++)
	{
		// calculate position based on threads id
		// check if the position is within a cube_face
		// write into ray_direction
		int lpos = (f * blockDim.x + threadIdx.x);
		int x, y, z;
		get_new_coordinates(
			&x, &y, &z,
			coord_2, coord_1, coord_0,
			increments_0, increments_1, increments_2,
			lpos, theta, face);
		int label = 0;

		if (
			x < x_max && y < y_max && z < z_max &&
			x >= 0 && y >= 0 && z >= 0)
		{
			size_t cube_pos = INDEX_3D(
				z_max, y_max, x_max,
				z, y, x);
			label = (int)d_label_list[cube_pos];

			if (lpos < 2048)
			{
				// size_t gpos = blockIdx.x * diagonal + lpos;
				// d_ray_classes[gpos] = label;
				s_ray_classes[lpos] = label;
			}
		}
	}
	__syncthreads();

	// determine_boundaries_v3(s_ray_classes, boundaries, class_values, boundary_count);
	nIter = (int)((len_ray_classes + blockDim.x - 1) / blockDim.x);

	// for (int f = 0; f < nIter; f++)
	// {
	// int lpos = (f * blockDim.x + threadIdx.x);
	// // int lpos = (f + nIter*threadIdx.x);
	// int warpId = lpos / warpSize;
	// int laneId = lpos % warpSize;
	// if (lpos < len_ray_classes)
	// {
	// 	determine_boundaries(s_ray_classes, warpId * warpSize, boundaries, class_values, &boundary_count);
	// }
	// }
	//  __syncthreads();

	int local_count = 0;
	for (int f = 0; f < nIter; f++)
	{

		int lpos = (f * blockDim.x + threadIdx.x);
		determine_boundaries_nowarp(s_ray_classes, boundaries, class_values, &boundary_count, len_ray_classes, lpos);
	}
	__syncthreads();
}

// }
// }

// for (int f = 0; f < nIter; f++)
// {
// 	int lpos = (f * blockDim.x + threadIdx.x);
// 	int warpId = lpos / warpSize;
// 	int laneId = lpos % warpSize;
// 	if (lpos < diagonal)
// 	{
// 		determine_boundaries(s_ray_classes, warpId * warpSize, boundaries, class_values, &boundary_count);
// 	}
// }

// __shared__ int distances[32 * warpSize];
// int count = 0;
// nIter = (int)((diagonal + warpSize - 1) / warpSize);
// __syncthreads();
// for (int f = 0; f < nIter; f++)
// {
// 	int lpos = (f * blockDim.x + threadIdx.x);
// 	int warpId = lpos / warpSize;
// 	int laneId = lpos % warpSize;
// 	if (lpos < diagonal)
// 	{
// 		determine_boundaries(s_ray_classes, warpId * warpSize, boundaries, class_values, &boundary_count);
// 	}
// }

// 	int total_num = boundaries[count - 1];
// 	for (int j = 0; j < count; j++)
// 	{
// 		if (j == 0)
// 		{
// 			cr_l += boundaries[j];
// 		}
// 		else
// 		{
// 			if (class_values[j] == 3)
// 				cr_l += boundaries[j] - boundaries[j - 1];
// 			else if (class_values[j] == 1)
// 				li_l += boundaries[j] - boundaries[j - 1];
// 			else if (class_values[j] == 2)
// 				lo_l += boundaries[j] - boundaries[j - 1];
// 			else if (class_values[j] == 4)
// 				bu_l += boundaries[j] - boundaries[j - 1];
// 			else
// 			{
// 			}
// 		}
// 	}
// 	// if (id == 0)
// 	// {
// 	// 	printf("count=%d\n", count);
// 	// }
// 	float li_absorption = 0;
// 	float lo_absorption = 0;
// 	float cr_absorption = 0;
// 	float bu_absorption = 0;

// 	float total_length;
// 	get_distance_2(&total_length, total_num, increments[0], increments[1], increments[2], face);

// 	float cr_l_f = (total_length * cr_l) / ((float)total_num);
// 	float li_l_f = (total_length * li_l) / ((float)total_num);
// 	float lo_l_f = (total_length * lo_l) / ((float)total_num);
// 	float bu_l_f = (total_length * bu_l) / ((float)total_num);
// 	float absorption = coeff_li * li_l_f + coeff_lo * lo_l_f + coeff_cr * cr_l_f + coeff_bu * bu_l_f;

// 	d_result_list[index * len_coord_list * 2 + id] = absorption;

// if (threadIdx.x == 0)
// {
// 	for (int count; count < boundary_count; count++)
// 	{
// 		if (count == 0)
// 		{
// 			cr_l += boundaries[count];
// 		}
// 		else
// 		{
// 			int distance = boundaries[count] - boundaries[count - 1];
// 			if (class_values[count] == 3)
// 				cr_l += distance;
// 			else if (class_values[count] == 1)
// 				li_l += distance;
// 			else if (class_values[count] == 2)
// 				lo_l += distance;
// 			else if (class_values[count] == 4)
// 				bu_l += distance;
// 			else
// 			{
// 			}
// 		}
// 	}
// 	absorption = coeff_li * li_l + coeff_lo * lo_l + coeff_cr * cr_l + coeff_bu * bu_l;
// 	d_result_list[index * len_coord_list * 2 + id] = absorption;

// Only a fraction of the threads will calculate distances to reduce redundant work.
// if (laneId < boundary_count) {
//     calculate_distances(boundaries + warpId * 32, class_values + warpId * 32, boundary_count, distances + warpId * 32);
// }
// get_distance_2(&total_length, diagonal, increments[0], increments[1], increments[2], face);

__global__ void rt_gpu_absorption_shuffle(int8_t *d_label_list, int *d_coord_list, int *d_face, float *d_angles, float *d_increments, float *d_result_list, size_t index)
{
	// one thread to calculate the absorption factor of a crystal voxel
	// size_t id = blockIdx.x;
	size_t id = blockIdx.x * blockDim.x + threadIdx.x;
	if (id < 2 * len_coord_list)
	{

		// size_t blockId = blockIdx.x;
		int is_ray_incomming = id & 1;
		size_t pos = (id >> 1); /* the right shift operation effectively divided the value of id by 2 (since shifting the bits to the right by 1 is equivalent to integer division by 2).*/
		float increments[3];
		int face = 0;
		int coord[3];
		float theta, phi;

		// __shared__ int s_ray_classes[2048];
		// __shared__ int boundaries[128];
		// __shared__ int class_values[128];
		int boundaries[64];
		int class_values[64];

		// int boundaries_all[diagonal];
		// int class_values_all[2048];
		// __shared__ int boundary_count;
		int cr_l = 1;
		int li_l = 0;
		int bu_l = 0;
		int lo_l = 0;

		// Load coordinates
		coord[0] = d_coord_list[3 * pos + 0]; // z
		coord[1] = d_coord_list[3 * pos + 1]; // y
		coord[2] = d_coord_list[3 * pos + 2]; // x

		// Load face
		// face = d_face[index * len_coord_list * 2 + id];  // outside  for loop
		face = d_face[id]; // within  for loop

		// printf("index= %ld face=%d\n", index*len_coord_list*2 + id,face);

		// Load angle
		theta = d_angles[4 * index + 2 * is_ray_incomming]; // outside for loop
		// theta = d_angles[4 * blockIdx.y + 2 * is_ray_incomming]; // within for loop
		// phi = d_angles[4*blockIdx.y + 2*is_ray_incomming + 1];

		// Load Increment
		size_t incr_pos = 36 * index + 18 * is_ray_incomming + 3 * (face - 1); // outside for loop
		// size_t incr_pos = 36 * blockIdx.y + 18 * is_ray_incomming + 3 * (face - 1); //within for loop

		// get_increment_ratio(&increments[0], &increments[1], &increments[2], theta, phi, face);
		increments[0] = d_increments[incr_pos + 0];
		increments[1] = d_increments[incr_pos + 1];
		increments[2] = d_increments[incr_pos + 2];

		// Calculate number of iterations of blocks
		// trick for ceiling

		int previous_label = 3;
		int count = 1;
		int label = 0;
		boundaries[0]=1;
		class_values[0]=3;
		for (int i = 0; i < diagonal; i++)
		{
			int x, y, z;
			get_new_coordinates(
				&x, &y, &z,
				coord[2], coord[1], coord[0],
				increments[0], increments[1], increments[2],
				i, theta, face);


			if (
				x < x_max && y < y_max && z < z_max &&
				x >= 0 && y >= 0 && z >= 0)
			{
				size_t cube_pos = INDEX_3D(
					z_max, y_max, x_max,
					z, y, x);

				label = (int)d_label_list[cube_pos];

				// class_values_all[i] = label;

				if (label != previous_label)
				{
					boundaries[count] = i;
					class_values[count] = previous_label;
					previous_label = label;
					
					count++;
				}

				if (label == 0)
				{

					break;
				}
			}
		}


		int total_num = boundaries[count - 1];
		for (int j = 0; j < count; j++)
		{
			if (j > 0){

				if (class_values[j] == 3)
					cr_l += boundaries[j] - boundaries[j - 1];
				else if (class_values[j] == 1)
					li_l += boundaries[j] - boundaries[j - 1];
				else if (class_values[j] == 2)
					lo_l += boundaries[j] - boundaries[j - 1];
				else if (class_values[j] == 4)
					bu_l += boundaries[j] - boundaries[j - 1];
				else
				{
				}
			}
		}
		// if (id == 0)
		// {
		// 	printf("count=%d\n", count);
		// }
		float li_absorption = 0;
		float lo_absorption = 0;
		float cr_absorption = 0;
		float bu_absorption = 0;

		float total_length;
		get_distance_2(&total_length, total_num, increments[0], increments[1], increments[2], face);

		float cr_l_f = (total_length * cr_l) / ((float)total_num);
		float li_l_f = (total_length * li_l) / ((float)total_num);
		float lo_l_f = (total_length * lo_l) / ((float)total_num);
		float bu_l_f = (total_length * bu_l) / ((float)total_num);
		float absorption = coeff_li * li_l_f + coeff_lo * lo_l_f + coeff_cr * cr_l_f + coeff_bu * bu_l_f;

		d_result_list[index * len_coord_list * 2 + id] = absorption;
	}
    	// Only a fraction of the threads will calculate distances to reduce redundant work.
	// if (laneId < boundary_count) {
	//     calculate_distances(boundaries + warpId * 32, class_values + warpId * 32, boundary_count, distances + warpId * 32);
	// }
	// get_distance_2(&total_length, diagonal, increments[0], increments[1], increments[2], face);

	// float cr_l = (total_length * cr_l_2_int) / ((float)diagonal);
	// float li_l = (total_length * li_l_2_int) / ((float)diagonal);
	// float lo_l = (total_length * lo_l_2_int) / ((float)diagonal);
	// float bu_l = (total_length * bu_l_2_int) / ((float)diagonal);

	// float absorption = 0;
	// float li_absorption = 0;
	// float lo_absorption = 0;
	// float cr_absorption = 0;
	// float bu_absorption = 0;
	// s_absorption[threadIdx.x] = coeff_li * li_l + coeff_lo * lo_l + coeff_cr * cr_l + coeff_bu * bu_l;

	// __syncthreads();
	// absorption = Reduce_SM(s_absorption);

	// Reduce_WARP(&absorption);

	// __syncthreads();

	// calculation of the absorption for given ray

	// }
}
