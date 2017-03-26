import json


class DataManager:

    class InvalidMap(Exception):
        pass

    @staticmethod
    def get(path):
        """Gets statistics from file"""
        try:
            with open(path) as ff:
                restored = json.load(ff)
                return restored
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            raise DataManager.InvalidMap

    @staticmethod
    def save(data, path):
        """Saves statistics to file"""
        with open(path, 'w') as ff:
            json.dump(data, ff)
