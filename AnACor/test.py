import os

paths = [
    "./3p0_4/11e51352-2757-4efd-9c1d-bbe6112d0b03/xia2-dials/DataFiles/cm37273v1_x3p04_scaled.refl",
    "./3p0_4/11e51352-2757-4efd-9c1d-bbe6112d0b03/xia2-dials/DataFiles/cm37273v1_x3p04_SAD_SWEEP1.refl",
    "./3p0_4/607997eb-b08b-4812-9b18-de06af5dbba0/xia2-dials/DataFiles/cm37273v1_x3p04_scaled.refl",
    "./3p0_4/607997eb-b08b-4812-9b18-de06af5dbba0/xia2-dials/DataFiles/cm37273v1_x3p04_SAD_SWEEP1.refl",
    "./3p5_1/43a5dd73-db37-46fd-8a20-31144e6cb956/xia2-dials/DataFiles/cm37273v1_x3p51_SAD_SWEEP1.refl",
    "./3p5_1/43a5dd73-db37-46fd-8a20-31144e6cb956/xia2-dials/DataFiles/cm37273v1_x3p51_scaled.refl",
    "./3p5_1/f1294784-58de-4672-960c-e137d21489e8/xia2-dials/DataFiles/cm37273v1_x3p51_SAD_SWEEP1.refl",
    "./3p5_1/f1294784-58de-4672-960c-e137d21489e8/xia2-dials/DataFiles/cm37273v1_x3p51_scaled.refl",
    "./3p5_4/0b9472de-26db-4753-a9c5-a593b7f373a3/xia2-dials/DataFiles/cm37273v1_x3p54_scaled.refl",
    "./3p5_4/0b9472de-26db-4753-a9c5-a593b7f373a3/xia2-dials/DataFiles/cm37273v1_x3p54_SAD_SWEEP1.refl",
    "./3p5_4/eb54da6e-bdec-49fa-9078-d216a8938e4a/xia2.multiplex/scaled.refl",
    "./3p5_4/70396634-b7ab-4d63-a37e-8c2af6219479/xia2-dials/DataFiles/cm37273v1_x3p54_scaled.refl",
    "./3p5_4/70396634-b7ab-4d63-a37e-8c2af6219479/xia2-dials/DataFiles/cm37273v1_x3p54_SAD_SWEEP1.refl"
]
# Base path to prepend
base_path = "/dls/i23/data/2024/cm37273-1/processed/TestThermolysin/tlys_2"

# Generate the updated list of paths
updated_paths = []
for path in paths:
    # Keep only the part before "xia2-dials" or "xia2.multiplex"
    if "xia2-dials" in path:
        cutoff_index = path.index("xia2-dials")
    else:
        continue
    
    # Join the base path with the truncated relative path
    new_path = os.path.join(base_path, path[:cutoff_index])
    updated_paths.append(new_path)

# Remove duplicates (if any) and sort the list
updated_paths = sorted(set(updated_paths))

# Print the final list
for updated_path in updated_paths:
    print(updated_path)
