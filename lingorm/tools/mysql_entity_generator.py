import sys
import os
import re
import pymysql


class MysqlEntityGenerator:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def generate(self, database, table_name=None, file_dir=None):
        if table_name is not None:
            self.__generate_entity(database, table_name, file_dir)
            print("table [" + table_name + "] generated\n")
        else:
            table_list = self.__get_tables(database)
            for row in table_list:
                self.__generate_entity(database, row["Table_name"], file_dir)
                print("table [" + row["Table_name"] + "] generated\n")

    def __generate_entity(self, database, table_name, file_dir):
        entity_name = self.__get_entity_name(table_name)
        entity_content = self.__get_template()
        if entity_content is None:
            raise Exception("Invalid template")

        entity_content = re.sub(
            "\\{\\{database_name\\}\\}", database, entity_content)
        entity_content = re.sub(
            "\\{\\{table_name\\}\\}", table_name, entity_content)
        entity_content = re.sub(
            "\\{\\{class_name\\}\\}", entity_name, entity_content)

        reg_property = r"[\s]*<--column-->([\s\S]*)<--column-->"
        match_result = re.search(reg_property, entity_content, re.M | re.I)
        if match_result is None:
            raise Exception("Invalid template")
        column_content = match_result.group(1)

        reg_init = r"[\s]*<--column_init-->([\s\S]*)<--column_init-->"
        match_result = re.search(reg_init, entity_content, re.M | re.I)
        if match_result is None:
            raise Exception("Invalid template")
        column_init_content = match_result.group(1)

        column_list = self.__get_columns(database, table_name)
        property_content = ""
        property_init_content = ""
        for column in column_list:
            column_property = 'field_name="' + column["COLUMN_NAME"] + '"'
            data_type = self.__get_data_type(column["DATA_TYPE"])
            column_property += ', field_type="' + data_type + '"'
            if data_type == "string" and column["CHARACTER_MAXIMUM_LENGTH"] is not None:
                column_property += ', length="' + \
                    str(column["CHARACTER_MAXIMUM_LENGTH"]) + '"'
            if column["COLUMN_KEY"] == "PRI":
                column_property += ', is_primary=True'
            if column["EXTRA"] == "auto_increment":
                column_property += ', is_generated=True'

            temp_property_content = column_content
            lower_property_name = self.__get_lower_property_name(column["COLUMN_NAME"])
            temp_property_content = re.sub(
                "\\{\\{lower_property_name\\}\\}", lower_property_name, temp_property_content)

            small_hump_property_name = self.__get_small_hump_property_name(column["COLUMN_NAME"])
            temp_property_content = re.sub(
                "\\{\\{small_hump_property_name\\}\\}", small_hump_property_name, temp_property_content)

            big_hump_property_name = self.__get_big_hump_property_name(column["COLUMN_NAME"])
            temp_property_content = re.sub(
                "\\{\\{big_hump_property_name\\}\\}", big_hump_property_name, temp_property_content)

            temp_property_content = re.sub(
                "\\{\\{column_property\\}\\}", column_property, temp_property_content)
            property_content += temp_property_content.strip(
                " ").strip("\r\n") + "\n"

            temp_init_content = column_init_content
            temp_init_content = re.sub(
                "\\{\\{lower_property_name\\}\\}", lower_property_name, temp_init_content)
            temp_init_content = re.sub(
                "\\{\\{small_hump_property_name\\}\\}", small_hump_property_name, temp_init_content)
            temp_init_content = re.sub(
                "\\{\\{big_hump_property_name\\}\\}", big_hump_property_name, temp_init_content)
            property_init_content += temp_init_content.strip(
                " ").strip("\r\n") + "\n"

        entity_content = re.sub(reg_property, "\n" +
                                property_content, entity_content)
        entity_content = re.sub(
            reg_init, "\n" + property_init_content, entity_content)
        entity_content = entity_content.strip("\n ")
        self.__save_entity(entity_name, entity_content, file_dir)

    def __get_tables(self, database):
        sql = "select Table_name from TABLES where TABLE_SCHEMA='" + database + "'"
        result = self.__fetch_all(sql)
        return result

    def __get_columns(self, database, table_name):
        sql = "select Column_name,DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,COLUMN_KEY,EXTRA from COLUMNS " \
              "where TABLE_SCHEMA='" + database + "' and Table_name='" + table_name + "'"
        result = self.__fetch_all(sql)
        return result

    def __get_data_type(self, field_type):
        field_type = field_type.lower()
        string_type = ("char", "varchar", "nvarchar")
        text_type = ("text", "longtext", "tinytext", "mediumtest")
        int_type = ("int", "smallint", "tinyint", "bigint", "mediumint")
        datetime_type = ("datetime", "date", "time", "timestamp", "year")
        float_type = ("double", "decimal", "float")

        if field_type in string_type:
            return "string"
        elif field_type in text_type:
            return "text"
        elif field_type in int_type:
            return "int"
        elif field_type in datetime_type:
            return "datetime"
        elif field_type in float_type:
            return "float"
        return "string"

    def __save_entity(self, entity_name, content, file_dir):
        if file_dir is None:
            file_dir = sys.path[0] + "/entity_generated"
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        filename = file_dir + "/" + \
            self.__get_file_name(entity_name) + "_entity.py"
        fp = open(filename, "w")
        fp.write(content)
        fp.close()

    def __get_template(self):
        filename = os.path.abspath(os.path.dirname(__file__)) + "/entity_template.py"
        print(filename)
        if not os.path.exists(filename):
            raise Exception("Template not found")
        fp = open(filename, "r")
        result = fp.read()
        fp.close()
        if result is not None:
            result = re.sub(r"\# ", "", result)
            result = re.sub(r"\#", "", result)
        return result

    def __get_file_name(self, table_name):
        result = re.sub(r'([^A-Z]*)([A-Z]{1})',
                        self.__file_name_deal, table_name)
        result = result.strip("_")
        return result

    def __file_name_deal(self, matched):
        return matched.group(1) + "_" + matched.group(2).lower()

    def __get_entity_name(self, field_name):
        result = re.sub(r'[_\\-]+([^_\\-]{1})', self.__name_upper_deal, field_name)
        result = result[0].upper() + result[1:]
        return result

    def __get_small_hump_property_name(self, field_name):
        result = re.sub(r'[_\\-]+([^_\\-]{1})', self.__name_upper_deal, field_name)
        result = result[0].lower() + result[1:]
        return result

    def __get_big_hump_property_name(self, field_name):
        result = re.sub(r'[_\\-]+([^_\\-]{1})', self.__name_upper_deal, field_name)
        result = result[0].upper() + result[1:]
        return result

    def __get_lower_property_name(self, field_name):
        result = re.sub(r'[_\\-]+([^_\\-]{1})', self.__name_lower_deal, field_name)
        result = result[0].lower() + result[1:]
        return result

    def __name_upper_deal(self, matched):
        val = matched.group(1)
        return val.upper()

    def __name_lower_deal(self, matched):
        val = matched.group(0)
        return val.lower()

    # data base
    def __get_connection(self):
        connection = pymysql.connect(
            host=self.host, user=self.user, passwd=self.password, db="information_schema", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor
        )
        return connection

    def __fetch_all(self, sql, param_dict=None):
        connection = self.__get_connection()
        cursor = connection.cursor()
        cursor.execute(sql, param_dict)
        result = cursor.fetchall()
        connection.commit()
        cursor.close()
        return result
