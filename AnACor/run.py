import sys
import os
import AnACor.preprocess_lite as preprocess_lite
import AnACor.mp_lite as mp_lite
import pdb
def main():
    # Step 0: Run preprocess_lite and get all preprocessed paths
    selected_paths,all_preprocessed_path = preprocess_lite.main()

    # Let the user check if all_preprocessed_path is correct
    print("Here are the preprocessed paths:")
    for path in selected_paths:
        print(path)

    user_input = input("Are these paths correct? (y/n): ")
    if user_input.lower() not in ['y', 'yes', 'ok', 'sure']:
        print("Exiting. Please verify the paths.")
        return

    # 
    for path in all_preprocessed_path:
        print(f"Processing: {path}")

        # Step 2: Set the new sys.path to the subpath of all_preprocessed_path
        # if os.path.isdir(path):
            # sys.path.insert(0, path)  # Add the path to sys.path
            # os.chdir(path)  
        # pdb.set_trace()
        try:
            # Step 3: Run mp_lite.main() for each path
            mp_lite.main(input_file=path)
        except Exception as e:
            
            # print(f"Error occurred while processing {path}: {e}")
            RuntimeError(f"Error occurred while processing {path}: {e}")
        finally:
            # Remove the path from sys.path after processing
            if path in sys.path:
                sys.path.remove(path)

        # else:
        #     print(f"Skipping {path} as it is not a valid directory.")

if __name__ == "__main__":
    main()