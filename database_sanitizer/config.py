# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import importlib

import six
import yaml

__all__ = ("Configuration", "ConfigurationError")

MYSQLDUMP_DEFAULT_PARAMETERS = ["--single-transaction"]
PG_DUMP_DEFAULT_PARAMETERS = []


class ConfigurationError(ValueError):
    """
    Custom exception type used to indicate configuration file errors.
    """


class Configuration(object):
    """
    Object representation of database sanitizer configuration, usually read
    from a YAML file.
    """
    def __init__(self):
        self.sanitizers = {}
        self.addon_packages = []
        self.mysqldump_params = []
        self.pg_dump_params = []

    @classmethod
    def from_file(cls, filename):
        """
        Reads configuration from given path to a file in local file system and
        returns parsed version of it.

        :param filename: Path to the YAML file in local file system where the
                         configuration will be read from.
        :type filename: str

        :return: Configuration instance parsed from given configuration file.
        :rtype: Configuration
        """
        instance = cls()

        with open(filename, "rb") as file_stream:
            config_data = yaml.load(file_stream)

        instance.load(config_data)

        return instance

    def load(self, config_data):
        """
        Loads sanitizers according to rulesets defined in given already parsed
        configuration file.

        :param config_data: Already parsed configuration data, as dictionary.
        :type config_data: dict[str,any]
        """
        if not isinstance(config_data, dict):
            raise ConfigurationError(
                "Configuration data is %s instead of dict." % (
                    type(config_data),
                )
            )

        self.load_addon_packages(config_data)
        self.load_sanitizers(config_data)
        self.load_dump_extra_parameters(config_data)

    def load_dump_extra_parameters(self, config_data):
        """
        Loads extra parameters for mysqldump and/or pg_dump CLI usage. These
        parameters should be added to the mysqldump and/or pg_dump command call
        when taking a dump.

        :param config_data: Already parsed configuration data, as dictionary.
        :type config_data: dict[str,any]
        """
        section_config = config_data.get("config", {})
        if not isinstance(section_config, dict):
            raise ConfigurationError(
                "'config' is %s instead of dict" % (
                    type(section_config),
                ),
            )

        section_extra_parameters = section_config.get("extra_parameters", {})
        if not isinstance(section_extra_parameters, dict):
            raise ConfigurationError(
                "'config.extra_parameters' is %s instead of dict" % (
                    type(section_extra_parameters),
                ),
            )

        mysqldump_params = section_extra_parameters.get("mysqldump", MYSQLDUMP_DEFAULT_PARAMETERS)
        if not isinstance(mysqldump_params, list):
            raise ConfigurationError(
                "'config.extra_parameters.mysqldump' is %s instead of list" % (
                    type(mysqldump_params),
                ),
            )

        pg_dump_params = section_extra_parameters.get("pg_dump", PG_DUMP_DEFAULT_PARAMETERS)
        if not isinstance(pg_dump_params, list):
            raise ConfigurationError(
                "'config.extra_parameters.pg_dump' is %s instead of list" % (
                    type(pg_dump_params),
                ),
            )

        self.mysqldump_params = mysqldump_params
        self.pg_dump_params = pg_dump_params

    def load_addon_packages(self, config_data):
        """
        Loads the module paths from which the configuration will attempt to
        load sanitizers from. These must be stored as a list of strings under
        "config.addons" section of the configuration data.

        :param config_data: Already parsed configuration data, as dictionary.
        :type config_data: dict[str,any]
        """
        section_config = config_data.get("config")
        if not isinstance(section_config, dict):
            if section_config is None:
                return
            raise ConfigurationError(
                "'config' is %s instead of dict" % (
                    type(section_config),
                ),
            )

        section_addons = section_config.get("addons", [])
        if not isinstance(section_addons, list):
            raise ConfigurationError(
                "'config.addons' is %s instead of list" % (
                    type(section_addons),
                ),
            )

        for index, module_path in enumerate(section_addons):
            if not isinstance(module_path, str):
                raise ConfigurationError(
                    "Item %d in 'config.addons' is %s instead of string" % (
                        index,
                        type(module_path),
                    ),
                )

        self.addon_packages = list(section_addons)

    def load_sanitizers(self, config_data):
        """
        Loads sanitizers possibly defined in the configuration under dictionary
        called "strategy", which should contain mapping of database tables with
        column names mapped into sanitizer function names.

        :param config_data: Already parsed configuration data, as dictionary.
        :type config_data: dict[str,any]
        """
        section_strategy = config_data.get("strategy")
        if not isinstance(section_strategy, dict):
            if section_strategy is None:
                return
            raise ConfigurationError(
                "'strategy' is %s instead of dict" % (
                    type(section_strategy),
                ),
            )

        for table_name, column_data in six.iteritems(section_strategy):
            if not isinstance(column_data, dict):
                if column_data is None:
                    continue
                raise ConfigurationError(
                    "'strategy.%s' is %s instead of dict" % (
                        table_name,
                        type(column_data),
                    ),
                )

            for column_name, sanitizer_name in six.iteritems(column_data):
                if sanitizer_name is None:
                    continue

                if not isinstance(sanitizer_name, str):
                    raise ConfigurationError(
                        "'strategy.%s.%s' is %s instead of string" % (
                            table_name,
                            column_name,
                            type(sanitizer_name),
                        ),
                    )

                sanitizer_callback = self.find_sanitizer(sanitizer_name)
                sanitizer_key = "%s.%s" % (table_name, column_name)
                self.sanitizers[sanitizer_key] = sanitizer_callback

    def find_sanitizer(self, name):
        """
        Searches for a sanitizer function with given name. The name should
        contain two parts separated from each other with a dot, the first
        part being the module name while the second being name of the function
        contained in the module, when it's being prefixed with "sanitize_".

        The lookup process consists from three attempts, which are:

        1. First package to look the module will be top level package called
           "sanitizers".
        2. Module will be looked under the "addon" packages, if they have been
           defined.
        3. Finally the sanitation function will be looked from the builtin
           sanitizers located in "database_sanitizer.sanitizers" package.

        If none of these provide any results, ConfigurationError will be
        thrown.

        :param name: "Full name" of the sanitation function containing name
                     of the module as well as name of the function.
        :type name: str

        :return: First function which can be imported with the given name.
        :rtype: callable
        """
        # Split the sanitizer name into two parts, one containing the Python
        # module name, while second containing portion of the function name
        # we are looking for.
        name_parts = name.split(".")
        if len(name_parts) < 2:
            raise ConfigurationError(
                "Unable to separate module name from function name in '%s'" % (
                    name,
                ),
            )

        module_name_suffix = ".".join(name_parts[:-1])
        function_name = "sanitize_%s" % (name_parts[-1],)

        # Phase 1: Look for custom sanitizer under a top level package called
        # "sanitizers".
        module_name = "sanitizers.%s" % (module_name_suffix,)
        callback = self.find_sanitizer_from_module(
            module_name=module_name,
            function_name=function_name,
        )
        if callback:
            return callback

        # Phase 2: Look for the sanitizer under "addon" packages, if any of
        # such have been defined.
        for addon_package_name in self.addon_packages:
            module_name = "%s.%s" % (
                addon_package_name,
                module_name_suffix,
            )
            callback = self.find_sanitizer_from_module(
                module_name=module_name,
                function_name=function_name,
            )
            if callback:
                return callback

        # Phase 3: Look from builtin sanitizers.
        module_name = "database_sanitizer.sanitizers.%s" % (module_name_suffix,)
        callback = self.find_sanitizer_from_module(
            module_name=module_name,
            function_name=function_name,
        )
        if callback:
            return callback

        # Give up.
        raise ConfigurationError("Unable to find sanitizer called '%s'" % (
            name,
        ))

    @staticmethod
    def find_sanitizer_from_module(module_name, function_name):
        """
        Attempts to find sanitizer function from given module. If the module
        cannot be imported, or function with given name does not exist in it,
        nothing will be returned by this method. Otherwise the found sanitizer
        function will be returned.

        :param module_name: Name of the module to import the function from.
        :type module_name: str

        :param function_name: Name of the function to look for inside the
                              module.
        :type function_name: str

        :return: Sanitizer function found from the module, if it can be
                 imported and it indeed contains function with the given name.
                 Otherwise None will be returned instead.
        :rtype: callback|None
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return None

        # Look for the function inside the module. At this point it could be
        # pretty much anything.
        callback = getattr(module, function_name, None)

        # Function does not exist in this module? Give up.
        if callback is None:
            return None

        # It's actually callable function? Return it.
        if callable(callback):
            return callback

        # Sanitizer seems to be something else than a function. Throw an
        # exception to report such problem.
        raise ConfigurationError("'%s' in '%s' is %s instead of function" % (
            function_name,
            module_name,
            type(callback),
        ))

    def get_sanitizer_for(self, table_name, column_name):
        """
        Get sanitizer for given table and column name.

        :param table_name: Name of the database table.
        :type table_name: str

        :param column_name: Name of the database column.
        :type column_name: str

        :return: Sanitizer function or None if nothing is configured
        :rtype: Optional[Callable[[Optional[str]], Optional[str]]]
        """
        sanitizer_key = "%s.%s" % (table_name, column_name)
        return self.sanitizers.get(sanitizer_key)

    def sanitize(self, table_name, column_name, value):
        """
        Sanitizes given value extracted from the database according to the
        sanitation configuration.

        TODO: Add support for dates, booleans and other types found in SQL than
        string.

        :param table_name: Name of the database table from which the value is
                           from.
        :type table_name: str

        :param column_name: Name of the database column from which the value is
                            from.
        :type column_name: str

        :param value: Value from the database, either in text form or None if
                      the value is null.
        :type value: str|None

        :return: Sanitized version of the given value.
        :rtype: str|None
        """
        sanitizer_callback = self.get_sanitizer_for(table_name, column_name)
        return sanitizer_callback(value) if sanitizer_callback else value
