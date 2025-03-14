
# ---------------------- TEMPORARY FUNCTION ------------------------------------
# A function which reads the content of the input file we are using as temporary input information.
def read_input_file(input_file_path):
    try:
        with open(input_file_path, 'r') as file:
            content = file.read()
            print("\nFile contents:")
            print(content)

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except IOError as e:
        print(f"Error opening file: {e}")


if __name__ == "__main__":
    file_path = input("Please enter the file path: ")
    read_input_file(file_path)
