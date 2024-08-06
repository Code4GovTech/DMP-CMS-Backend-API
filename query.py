from db import SupabaseInterface
from models import *
from sqlalchemy import func

class PostgresQuery:

    def get_issue_query():
        query = """
            SELECT 
                dmp_orgs.id AS org_id, 
                dmp_orgs.name AS org_name,
                json_agg(
                    json_build_object(
                        'id', dmp_issues.id,
                        'name', dmp_issues.title
                )
                ) AS issues
            FROM 
                dmp_orgs
            LEFT JOIN 
                dmp_issues 
            ON 
                dmp_orgs.id = dmp_issues.org_id
            GROUP BY 
                dmp_orgs.id
            ORDER BY 
               dmp_orgs.id;
        """
        
        data = SupabaseInterface.postgres_query(query)
        return data
        
    def get_issue_owner(name):
        query = """
            SELECT name, description
            FROM dmp_orgs
            WHERE name = %s;
        """
        data = SupabaseInterface.postgres_query(query,(name,))
        return data
    
    def get_actual_owner_query(owner):
        query = """
            SELECT id, name, repo_owner
            FROM dmp_orgs
            WHERE name LIKE %s;
        """
        
        data = SupabaseInterface.postgres_query(query,(f'%{owner}%',))
        return data
    
     
    def get_dmp_issues(issue_id):
        
        query = """
                SELECT * FROM dmp_issues
                WHERE id = %s;
        """
        data = SupabaseInterface.postgres_query(query,(issue_id,))
        return data
        
    def get_dmp_issue_updates(dmp_issue_id):

        query = """
                SELECT * FROM dmp_issue_updates
                WHERE dmp_id = %s;
        """
        data = SupabaseInterface.postgres_query(query,(dmp_issue_id,))
        return data
        
    
    def get_pr_data(dmp_issue_id):

        query = """
                SELECT * FROM dmp_pr_updates
                WHERE dmp_id = %s;
        """
        data = SupabaseInterface.postgres_query(query,(dmp_issue_id,))
        return data
    
    

class PostgresORM:

    def get_issue_query():
        results = (
            db.session.query(
                DmpOrg.id.label('org_id'),
                DmpOrg.name.label('org_name'),
                func.json_agg(
                    func.json_build_object(
                        'id', DmpIssue.id,
                        'name', DmpIssue.title
                    )
                ).label('issues')
            )
            .outerjoin(DmpIssue, DmpOrg.id == DmpIssue.org_id)
            .group_by(DmpOrg.id)
            .order_by(DmpOrg.id)
            .all()
        )
        
        return results
        
    def get_issue_owner(name):        
        response = DmpOrg.query.filter_by(name=name).all()
        return response
    
    def get_actual_owner_query(owner):
        results = DmpOrg.query.filter(DmpOrg.name.like(f'%{owner}%')).all()
        results = [val.to_dict() for val in results]
        return results
    
     
    def get_dmp_issues(issue_id):        
        results = DmpIssue.query.filter_by(id=issue_id).all()
        results = [val.to_dict() for val in results]
        return results
        
        
    def get_dmp_issue_updates(dmp_issue_id):        
        results = DmpIssueUpdate.query.filter_by(dmp_id=dmp_issue_id).all()
        results = [val.to_dict() for val in results]
        return results
        
    
    def get_pr_data(dmp_issue_id):       
        pr_updates = Prupdates.query.filter_by(dmp_id=dmp_issue_id).all()
        pr_updates_dict = [pr_update.to_dict() for pr_update in pr_updates]
        return pr_updates_dict
        
                