import numpy as np
import pdb
#This data is extracted from the table in the International Table
# Maslen, E. N. (2006). International Tables for Crystallography, volume C, chapter 6.3.3, Absorption corrections, pages600–608. 3rd edition.
# https://it.iucr.org/Cb/ch6o3v0001/sec6o3o1/


def Sphere ( radius , pixel_size , sphere_value ) :
    
    # https://stackoverflow.com/questions/64212348/creating-a-sphere-at-center-of-array-without-a-for-loop-with-meshgrid-creates-sh

    num_pix =  int((radius/pixel_size) *3 )
    Radius_sq_pixels = int((radius/pixel_size) ** 2)

    center_pixel = int( num_pix / 2 - 1 )
    new_array = np.zeros( (num_pix , num_pix , num_pix) ,dtype=np.int8)

    m , n , r = new_array.shape
    x = np.arange( 0 , m , 1 )
    y = np.arange( 0 , n , 1 )
    z = np.arange( 0 , r , 1 )

    xx , yy , zz = np.meshgrid( x , y , z , indexing = 'ij' , sparse = True )
    X = (xx - center_pixel)
    Y = (yy - center_pixel)
    Z = (zz - center_pixel)

    mask = ((X ** 2) + (Y ** 2) + (Z ** 2)) < Radius_sq_pixels  # create sphere mask
    new_array = sphere_value * mask  # assign values
    new_array = new_array.astype( np.uint8 )  # change datatype
  
    # import matplotlib.pyplot as plt
    # from skimage import measure
    #
    # fig = plt.figure( )
    # ax = fig.add_subplot( 1 , 1 , 1 , projection = '3d' )
    #
    # verts , faces , normals , values = measure.marching_cubes( new_array,0.1)
    #
    # ax.plot_trisurf(
    #     verts[: , 0] , verts[: , 1] , faces , verts[: , 2] , cmap = 'Spectral' ,
    #     antialiased = False , linewidth = 0.0 )
    # ax.set_ylabel('y')
    # ax.set_zlabel( 'z' )
    # ax.set_xlabel( 'x' )
    # ax.view_init( 0 , 90 )
    # plt.show( )
    padding = 10
    padded_array = np.pad(new_array, pad_width=padding, mode='constant', constant_values=0)
    
    return padded_array



def Cylinder ( radius , pixel_size , sphere_value,length ) :
    # https://stackoverflow.com/questions/64212348/creating-a-sphere-at-center-of-array-without-a-for-loop-with-meshgrid-creates-sh
    length= int((length/pixel_size) )
    num_pix =  int((radius/pixel_size) *3 )
    Radius_sq_pixels = int((radius/pixel_size) ** 2)

    center_pixel = int( num_pix / 2 - 1 )
    new_array = np.zeros( (num_pix , num_pix , num_pix) )

    m , n , r = new_array.shape
    x = np.arange( 0 , m , 1 )
    y = np.arange( 0 , n , 1 )
    #z = np.arange( 0 , r , 1 )
    z = np.arange(center_pixel - int(np.floor(length/2)), center_pixel + int(np.ceil(length/2)), 1)
    # print("len of length is ",len(z))
    xx , yy , zz = np.meshgrid( x , y , z , indexing = 'ij' , sparse = True )
    xx , yy = np.meshgrid( x , y ,indexing = 'ij' , sparse = True )

    X = (xx - center_pixel)
    Y = (yy - center_pixel)
    Z = (zz - center_pixel)
 
    mask = ((X ** 2) + (Y ** 2) ) < Radius_sq_pixels  # create sphere mask
    new_array = sphere_value * np.stack([mask for _ in range(len(z))], axis=0)
    new_array = new_array.astype( np.uint8 )  # change datatype
    padding = 10
    padded_array = np.pad(new_array, pad_width=padding, mode='constant', constant_values=0)
    
    return padded_array
def extract_from_table(numbers):
    numbers = numbers[0::2]
    numbers=1/np.array(numbers)
    return numbers

cylinder_correct_p5=[2.2996, 2.2979, 2.2926, 2.2840, 2.2721, 2.2572, 2.2398, 2.2204, 2.1996, 2.1781, 2.1564, 2.1352, 2.1152, 2.0969, 2.0809, 2.0677, 2.0579, 2.0518, 2.0497]
cylinder_correct_1=[5.0907, 5.0724, 5.0185, 4.9323, 4.8196, 4.6877, 4.5439, 4.3948, 4.2461, 4.1022, 3.9664, 3.8413, 3.7286, 3.6298, 3.5462, 3.4790, 3.4295, 3.3990, 3.3886]
cylinder_correct_1p5=[10.746, 10.643, 10.349, 9.907, 9.372, 8.800, 8.230, 7.689, 7.192, 6.744, 6.348, 6.002, 5.7036, 5.4516, 5.2441, 5.0804, 4.9609, 4.8875, 4.8625]
cylinder_correct_p5=extract_from_table(cylinder_correct_p5)
cylinder_correct_1=extract_from_table(cylinder_correct_1)
cylinder_correct_1p5=extract_from_table(cylinder_correct_1p5)


sphere_correct_p1=[1.4845, 1.4842, 1.4829, 1.4809, 1.4782, 1.4739, 1.4690, 1.4634, 1.4569, 1.4504, 1.4439, 1.4375, 1.4309, 1.4248, 1.4191, 1.4152, 1.4117, 1.4096, 1.4089]
sphere_correct_p5=[2.0755, 2.0743, 2.0706, 2.0647, 2.0565, 2.0462, 2.0340, 2.0204, 2.0056, 1.9901, 1.9745, 1.9592, 1.9445, 1.9311, 1.9194, 1.9097, 1.9024, 1.8979, 1.8964]
sphere_correct_1=[4.1237, 4.1131, 4.0815, 4.0304, 3.9625, 3.8816, 3.7917, 3.6966, 3.6001, 3.5048, 3.4135, 3.3280, 3.2499, 3.1807, 3.1216, 3.0738, 3.0383, 3.0163, 3.0090]
sphere_correct_1p5=[7.801, 7.750, 7.604, 7.377, 7.092, 6.775, 6.447, 6.123, 5.8143, 5.5273, 5.2666, 5.0333, 4.8281, 4.6520, 4.5052, 4.3883, 4.3024, 4.2495, 4.2315]
sphere_correct_p1=extract_from_table(sphere_correct_p1)
sphere_correct_p5=extract_from_table(sphere_correct_p5)
sphere_correct_1=extract_from_table(sphere_correct_1)
sphere_correct_1p5=extract_from_table(sphere_correct_1p5)