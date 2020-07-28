import re
import requests
import zipfile

with open('dem_files.txt') as f:
    content = f.readlines()
content = [x.strip() for x in content] 

outpath = 'DEMfilesZip/'

for url in content:
    print(url)
    filename = url.split('/')[-1]
    path = outpath + filename

    r = requests.get(url, allow_redirects=True)
    open(path, 'wb').write(r.content)

    extract_path = 'DEMfiles/' + filename
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
