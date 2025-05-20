import os
import hashlib
import zipfile
import shutil
from ecc_signing_and_verify import ecc_signing_and_verify
class file_handling:
    def __init__(self):
        self.os=os
        self.hashlib=hashlib
        self.zipfile=zipfile
        self.shutil=shutil
        self.ecc_signing_and_verify=ecc_signing_and_verify()

        pass

    def sha256_checksum(self,filepath):
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def zip_multiple_files(self,file_list, zip_path):
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in file_list:
                zipf.write(file, arcname=file.split('/')[-1])
                print(f"[+] Added {file}")

    def unzip(self,zip_path, extract_to="./temp"):
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(path=extract_to)

    def split_file(self,filepath, chunk_size=1024 * 1024):
        print("Checksum:", self.sha256_checksum(filepath))
        with open("checksum.txt", 'w') as f:
            f.write(self.sha256_checksum(filepath))
        with open("file.sig", 'wb+') as f:
            f.write(self.ecc_signing_and_verify.sign(filepath))
        os.makedirs("temp", exist_ok=True)
        shutil.move("file.sig", "temp/file.sig")
        shutil.move("checksum.txt", "temp/checksum.txt")
        shutil.move(filepath, "temp/" + os.path.basename(filepath))
        file_list = ["temp/checksum.txt", "temp/" + os.path.basename(filepath),"temp/file.sig"]
        self.zip_multiple_files(file_list, "temp.zip")
        shutil.move("temp.zip", "temp/temp.zip")
        filename = os.path.basename("temp/temp.zip")
        filepath = os.path.join("temp", filename)

        with open(filepath, 'rb') as f:
            chunk_index = 0
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                chunk_name = f"{filename}.part{chunk_index:04d}"
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
                    print(f"[+] Wrote chunk: {chunk_name}")

                chunk_index += 1
        if os.path.exists(filepath):
            os.remove(filepath)
            #shutil.rmtree("temp")
            print("temp removed")

    def merge_chunks(self):
        chunk_index = 0
        base_filename = "temp.zip"
        output_filename = "temp.zip"

        # Merge chunks
        with open(output_filename, 'wb') as output_file:
            while True:
                chunk_name = f"{base_filename}.part{chunk_index:04d}"
                if not os.path.exists(chunk_name):
                    break
                with open(chunk_name, 'rb') as chunk_file:
                    output_file.write(chunk_file.read())
                    print(f"[+] Merged: {chunk_name}")
                os.remove(chunk_name)
                chunk_index += 1

        # Extract temp.zip
        self.unzip(output_filename)
        os.remove(output_filename)

        # Get file list before deleting anything
        files = os.listdir("temp")
        original_files = [f for f in files if f not in ["checksum.txt", "file.sig"]]

        # Read reference checksum
        with open("temp/checksum.txt", 'r') as f:
            expected_checksum = f.read().strip()

        # Read signature
        with open("temp/file.sig", 'rb') as f:
            signature = f.read()

        # Verify
        target_file = os.path.join("temp", original_files[0])
        actual_checksum = self.sha256_checksum(target_file)
        print(f"[+] Actual checksum: {actual_checksum}")

        if actual_checksum != expected_checksum:
            print("[X] Checksum mismatch – file was modified or corrupted!")
        elif not self.ecc_signing_and_verify.verify(target_file, signature):
            print("[X] Signature invalid – file not authentic!")
        else:
            print("[+] File verified successfully.")

        # Move verified file
        shutil.move(target_file, os.path.basename(target_file))

        # Cleanup
        shutil.rmtree("temp", ignore_errors=True)
        print("[+] Cleaned up temporary files.")


# Sample usage
file_handling=file_handling()
file_handling.split_file("File")
file_handling.merge_chunks()