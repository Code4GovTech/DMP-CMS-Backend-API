from flask import Flask, jsonify
from db import SupabaseInterface
from collections import defaultdict
from flasgger import Swagger


app = Flask(__name__)

Swagger(app)


@app.route('/api/greeting', methods=['GET'])
def greeting():
    """
    A simple greeting endpoint.
    ---
    responses:
      200:
        description: A greeting message
        schema:
          type: object
          properties:
            message:
              type: string
              example: Hello, welcome to my API!
    """
    response = {
        'message': 'Hello, welcome to my API!'
    }
    return jsonify(response)

@app.route('/api/get-data', methods=['GET'])
def get_data():
    """
    Fetch data from Supabase.
    ---
    responses:
      200:
        description: Data fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching data
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_pr_updates').select('*').execute()
        data = response.data
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def group_by_owner(data):
    grouped_data = defaultdict(list)
    for record in data:
      owner = record['owner']
      grouped_data[owner].append(record)
        
        
    #Arrange data as reponse format
    res = []
    for val in grouped_data:
      dict_ = {}
      dict_['org_name'] = val
      dict_['issues'] = grouped_data[val]
      
      res.append(dict_)
      
    return {"issues":res}

@app.route('/api/issues', methods=['GET'])
def get_issues():
    """
    Fetch all issues and group by owner.
    ---
    responses:
      200:
        description: Issues grouped by owner
        schema:
          type: object
          additionalProperties:
            type: array
            items:
              type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').execute()
        data = response.data
        grouped_data = group_by_owner(data)
        return jsonify(grouped_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/issues/<owner>', methods=['GET'])
def get_issues_by_owner(owner):
    """
    Fetch issues by owner.
    ---
    parameters:
      - name: owner
        in: path
        type: string
        required: true
        description: The owner of the issues
    responses:
      200:
        description: Issues fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).execute()
        if not response.data:
            return jsonify({'error': "No data found"}), 500
        data = response.data
        data = [{**item, "name": item["owner"]} for item in data]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/issues/<owner>/<issue>', methods=['GET'])
def get_issues_by_owner_id(owner, issue):
    """
    Fetch issues by owner and issue number.
    ---
    parameters:
      - name: owner
        in: path
        type: string
        required: true
        description: The owner of the issues
      - name: issue
        in: path
        type: string
        required: true
        description: The issue number
    responses:
      200:
        description: Issues fetched successfully
        schema:
          type: array
          items:
            type: object
      500:
        description: Error fetching issues
        schema:
          type: object
          properties:
            error:
              type: string
    """
    try:
        response = SupabaseInterface().get_instance().client.table('dmp_issue_updates').select('*').eq('owner', owner).eq('issue_number', issue).execute()
        if not response.data:
            return jsonify({'error': "No data found"}), 500
        data = response.data
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)