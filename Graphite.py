import configparser
import os

class GraphiteInter:
    @staticmethod
    def ReadIniFile(filepath, section, option):
        """
        Reads a value from an INI file under a specific section and option.
        """
        config = configparser.ConfigParser()
        # Ensure we read with UTF-8
        if os.path.exists(filepath):
            config.read(filepath, encoding='utf-8')
        else:
            return ""
        
        try:
            return config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return ""

    @staticmethod
    def Change_ini(filepath, section, option, value):
        """
        Changes/updates a value in an INI file under a specific section and option.
        Creates section and file if they don't exist.
        """
        config = configparser.ConfigParser()
        if os.path.exists(filepath):
            config.read(filepath, encoding='utf-8')
            
        if not config.has_section(section):
            config.add_section(section)
            
        config.set(section, option, str(value))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            config.write(f)
