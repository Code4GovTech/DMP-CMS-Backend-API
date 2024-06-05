import os, sys
from typing import Any
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from abc import ABC, abstractmethod

client_options = ClientOptions(postgrest_client_timeout=None)



class SupabaseInterface():
    
    _instance = None
    
    def __init__(self):
        if not SupabaseInterface._instance:
                        
            # Load environment variables
            from dotenv import load_dotenv
            load_dotenv()

            SUPABASE_URL = os.getenv('APP_DEV_SUPABASE_URL')
            SUPABASE_KEY = os.getenv('APP_DEV_SUPABASE_KEY')
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            SupabaseInterface._instance = self
        else:          
            SupabaseInterface._instance = self._instance
        
    

    @staticmethod
    def get_instance():
        # Static method to retrieve the singleton instance
        if not SupabaseInterface._instance:
            # If no instance exists, create a new one
            SupabaseInterface._instance = SupabaseInterface()
        return SupabaseInterface._instance
    
       
    def readAll(self, table):
        data = self.client.table(f"{table}").select("*").execute()
        return data.data
    
    def add_data(self, data,table_name):
        data = self.client.table(table_name).insert(data).execute()
        return data.data
    
    def add_data_filter(self, data, table_name):
        # Construct the filter based on the provided column names and values
        filter_data = {column: data[column] for column in ['dmp_id','issue_number','owner']}
        
        # Check if the data already exists in the table based on the filter
        existing_data = self.client.table(table_name).select("*").eq('dmp_id',data['dmp_id']).execute()

        # If the data already exists, return without creating a new record
        if existing_data.data:
            return "Data already exists"
        
        # If the data doesn't exist, insert it into the table
        new_data = self.client.table(table_name).insert(data).execute()
        return new_data.data