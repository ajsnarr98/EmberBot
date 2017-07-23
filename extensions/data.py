import json
import os
import pickle

data_dir = 'data' # this dir is placed in the parent dir of '/extensions'
json_dir = 'json' # this is a sub-dir of data_dir
pickle_dir = 'pickled' # this is a sub-dir of data_dir

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(project_dir, data_dir)
json_dir = os.path.join(data_dir, json_dir)
pickle_dir = os.path.join(data_dir, pickle_dir)

# create dirs if they do not exist
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
if not os.path.exists(json_dir):
    os.makedirs(json_dir)
if not os.path.exists(pickle_dir):
    os.makedirs(pickle_dir)

class DataManager(object):
    
    def __init__(self):
        pass

    def save_pickled(self, obj, filename):
        """ Pickles the given object and saves in data/filename. """
        path = os.path.join(pickle_dir, filename)
        with open(path, 'wb+') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


    def load_pickled(self, filename):
        """ Loads the pickled object from data/filename. """
        try:
            path = os.path.join(pickle_dir, filename)
            with open(path, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return None
            

    def save_json(self, obj, filename):
        """ Saves the given object in data/filename, in json format. """
        path = os.path.join(json_dir, filename)
        with open(path, 'w+') as f:
            json.dump(obj, f, indent=2)


    def load_json(self, filename):
        """ Loads the json-encoded object from data/filename. """
        try:
            path = os.path.join(json_dir, filename)
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, EOFError, json.decoder.JSONDecodeError):
            return None

    def walk_json(self):
        """ Equivalent to os.walk(json_dir). """
        for dirpath, dirnames, filenames in os.walk(json_dir):
            yield (dirpath, dirnames, filenames)