import os

# ---------------------- TEMPORARY FUNCTION ------------------------------------
# A function which reads the content of the input file we are using as temporary input information.
def read_input_file(input_file_path):
    try:
        with open(input_file_path, 'r') as file:
            lines = file.readlines()
            header = lines[0].strip()
            #TODO: pass the input data to the RRT* algorithm

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except IOError as e:
        print(f"Error opening file: {e}")


if __name__ == "__main__":
    # Install the required packages
    os.system('pip install -r requirements.txt')

    file_path = 'inputs.txt'
    read_input_file(file_path)
