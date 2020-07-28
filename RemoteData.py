from datetime import datetime
import os 
import urllib.request
import json

from aws_sat_api.search import landsat
import boto3
import botocore
import pandas


test_files = [
    'https://datapool.asf.alaska.edu/SLC/SB/S1B_IW_SLC__1SDV_20171117T145900_20171117T145928_008323_00EBAB_B716.zip',
    'https://datapool.asf.alaska.edu/SLC/SB/S1B_IW_SLC__1SDV_20171117T145926_20171117T145953_008323_00EBAB_AFB8.zip'
]


class PullerASF:

    def __init__(self):
        self.asf_user, self.asf_pass = self.get_credentials('ASF')

    def get_credentials(self, site):
        hdd_dir = os.getenv("HDD")
        creds_path = os.path.abspath(
            os.path.join(hdd_dir, "remote_sensing/credentials.json")
        )
        with open(creds_path) as jfile:
            data = json.load(jfile)

        return data[site]['username'], data['ASF']['password']

    def search_for_files(self, terms, outdir):
        """
        With a list of search terms will create api call to search database

        For a list of terms visit:
        https://asf.alaska.edu/api/

        Inputs-
        terms: Dictionary with key pairs of terms for api
        outtype: 
        """
        print('Searching for scenes with parameters:')
        print(terms)

        # Set-up for Results location
        search_dir = os.path.join(outdir, 'search_results')
        if not os.path.exists(search_dir):
            os.makedirs(search_dir)

        print('Placing search results at:')
        print(search_dir)

        # Create the API URL
        base_url = 'https://api.daac.asf.alaska.edu/services/search/param?'
        searchstr = ''
        for key, val in terms.items():
            searchstr += '{0}={1}\&'.format(key, val)
        url = base_url + searchstr + 'output=CSV'

        print('Calling API:')
        print(url)

        # Run the Command in terminal
        outfile = 'results.csv'
        outpath = os.path.join(search_dir, outfile)
        cmd = "wget -O {0} {1} --user={2} --password={3}".format(
            outpath,
            url,
            self.asf_user,
            self.asf_pass
        )
        print(cmd)
        os.system(cmd)

        # Read results to dataframe and filter necesary information
        df = pandas.read_csv(outpath)
        df = df[["Granule Name", "URL", "Start Time"]]

        print('Found {0} results'.format(len(df)))

        # Remove bulky results file and save slim results file
        os.system("rm {0}".format(outpath))
        df.to_csv(outpath, index=False)

        print('Wrote results to:')
        print(outpath)

        return outpath


    def get_files(self, files, outdir):
        """
        With a list of specific files, download into a directory

        Inputs-
        files: List of files or string of file
        outdir: Path to where you want to put the files

        Outputs-
        Sucess: did it succeed?
        """
        # Get Credentials
        cwd = os.getcwd()
        # Set and create save location
        slc_dir = os.path.join(outdir,'slc')
        if not os.path.exists(slc_dir):
            os.makedirs(slc_dir)

        if not isinstance(files, list):
            files = [files]

        for f in files:
            filename = os.path.basename(f)
            
            if not os.path.exists(os.path.join(slc_dir,filename)):
                print('Pulling file: {}'.format(f))
                cmd = "wget {0} --user={1} --password={2}".format(
                    f,
                    self.asf_user, 
                    self.asf_pass
                )
                os.chdir(slc_dir)
                os.system(cmd)

            else:
                print(filename + " already exists")
            os.chdir(cwd)

        return True


class PullerSentinel:

    def __init__(self):
        self.user, self.pw = self.get_credentials('ESA')

    def get_credentials(self, site):
        hdd_dir = os.getenv("HDD")
        creds_path = os.path.abspath(
            os.path.join(hdd_dir, "remote_sensing/credentials.json")
        )
        with open(creds_path) as jfile:
            data = json.load(jfile)

        return data[site]['username'], data['ASF']['password']

    def get_files(self, files, outdir):
        """
        With a list of specific files, download into a directory

        Inputs-
        files: List of files or string of file
        outdir: Path to where you want to put the files

        Outputs-
        Sucess: did it succeed?
        """
        print(self.user, self.pw)
        # Get Credentials
        cwd = os.getcwd()
        # Set and create save location
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if not isinstance(files, list):
            files = [files]

        for f in files:
            filename = os.path.basename(f)
            
            if not os.path.exists(os.path.join(outdir, filename)):
                print('Pulling file: {}'.format(f))
                cmd = "wget --content-disposition {0} --user={1} --password={2}".format(
                    f,
                    self.user, 
                    self.pw
                )
                os.chdir(outdir)
                os.system(cmd)

            else:
                print(filename + " already exists")
            os.chdir(cwd)

        return True


class PullerLansat8:

    def __init__(self):
        pass

    def find_scenes(self, path, row, full_search=True, 
                    clean=True, filt=True):
        
        results = [i for i in landsat(path, row, full_search)]
 
        if clean:
            results_post = pandas.DataFrame()
            for key in results:
                if not key['cloud_coverage_land']:
                    continue
                elif filt and float(key.get('cloud_coverage_land', 100)) > 10:
                    continue
                else:
                    key['acquisition_date'] = pandas.to_datetime(
                        key['acquisition_date'], 
                        format='%Y%m%d'
                    )
                    data = {
                        'satellite': [key['satellite']],
                        'date': [key['acquisition_date']],
                        'key': [key['key']],
                        'cloud_coverage_land': [key['cloud_coverage_land']],
                        'browseURL': [key['browseURL']]
                    }
                    results_post = results_post.append(
                        pandas.DataFrame(data=data)
                    )

        if not clean:
            results_post = results

        return results_post

    def download_from_list(self, keylist, opath, bands=[4, 3, 2]):
        """
        Download landsat files from list of files
        """
        s3 = boto3.resource('s3')
        bucket = 'landsat-pds'
#        opath = '/Volumes/EGG-HD/remote_sensing/testing/landsat/' # Testing
        for key in keylist:
            opath_key = os.path.join(opath, key.split('/')[-1])
            if not os.path.exists(opath_key):
                os.makedirs(opath_key)
            key_pure = key
            for band in bands:
                key = key_pure
                try:
                    key = key + '_B{}.TIF'.format(band)
                    fn = key.split('/')[-1]
                    print(key)
                    s3.Bucket(bucket).download_file(
                        key, 
                        os.path.join(opath_key, fn)
                    )
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        print("The object does not exist.")
                    else:
                        raise

    def download_from_csv(self, fpath, opath, bands=[4, 3, 2]):
        """
        Download landsat files from the csv output from find_scenes routine
        """
        s3 = boto3.resource('s3')
        bucket = 'landsat-pds'
#        opath = '/Volumes/EGG-HD/remote_sensing/testing/landsat/' # Testing

        df = pandas.read_csv(fpath)
        for idx, line in df.iterrows():
            opath = os.path.join(opath, key.split('/')[-1])
            if not os.path.exists(opath):
                os.makedirs(opath)
            for band in bands:
                try:
                    key = line['key'] + '_B{}.TIF'.format(band)
                    fn = key.split('/')[-1]
                    print(key)
                    s3.Bucket(bucket).download_file(
                        key, 
                        os.path.join(opath, fn)
                    )
                except botocore.exceptions.ClientError as e:
                    if e.response['Error']['Code'] == "404":
                        print("The object does not exist.")
                    else:
                        raise


if __name__ == '__main__':
    #Earthquake zone west
    l8_path = 160
    l8_row = 73
#    # EQ zone east
#    l8_path = 159
#    l8_row = 73
#    # North
#    l8_path = 159
#    l8_row = 72

    full_search = True
    puller = PullerLansat8()
    results = puller.find_scenes(l8_path, l8_row, filt=True)

    start_date = '12-01-2015'
    end_date = '03-01-2016'
    mask = (
        (results['date'] > start_date) 
        & (results['date'] <= end_date)
    )
    results_filt = results[mask]
    results_final = results_filt.iloc[4:]
    results_final = results_filt.iloc[2]

#    keylist = [results_final['key']]
    keylist = [
        'L8/159/073/LC81590732016281LGN00/LC81590732016281LGN00',
        'L8/160/073/LC81600732016304LGN00/LC81600732016304LGN00',
        'L8/159/072/LC81590722016281LGN00/LC81590722016281LGN00',
    ]

    opath = ''
    puller.download_from_list(keylist, opath, bands=[1, 2, 3, 4, 5])
