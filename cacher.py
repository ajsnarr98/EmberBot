import pickle

cachePath = 'data/cache.pkl'

def get(key: str):
    """ Gets object related to key str in cache dict.
        
        Keys should have naming convention:
            '<module>.<functionname>.<nameofthing>'


        returns the value associated with the key,
        or None if if does not exist
    """
    try:
        cache_dict = load_obj(cachePath)
        if type(cache_dict) == dict:
            return cache_dict.get(key, None)
        else:
            return None
    except FileNotFoundError:
        return None
    # If file is empty
    except EOFError:
        return None


def store(key: str, value):
    """ Stores given value with given key str in cache dict.
        
        Keys should have naming convention:
            '<module>.<functionname>.<nameofthing>'
    """
    try:
        cache_dict = load_obj(cachePath)
        if type(cache_dict) == dict:
            cache_dict[key] = value
            save_obj(cache_dict, cachePath)
        else:
            return None
    except (FileNotFoundError, EOFError):
        cache_dict = {key : value}
        save_obj(cache_dict, cachePath)


def save_obj(obj, name):
    with open(name, 'wb+') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)