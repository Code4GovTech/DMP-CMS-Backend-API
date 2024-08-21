from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class DmpOrg(db.Model):
    __tablename__ = 'dmp_orgs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String, nullable=False)
    repo_owner = db.Column(db.String, nullable=False)

    # Relationship to DmpIssueUpdate
    issues = db.relationship('DmpIssueUpdate', backref='organization', lazy=True)
    
    # Updated relationship name to avoid conflict
    dmp_issues = db.relationship('DmpIssue', backref='organization', lazy=True)
    
    def __repr__(self):
        return f"<DmpOrg(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'name': self.name,
            'description': self.description,
            'link': self.link,
            'repo_owner': self.repo_owner
        }

class DmpIssue(db.Model):
    __tablename__ = 'dmp_issues'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    issue_url = db.Column(db.String, nullable=False)
    issue_number = db.Column(db.Integer, nullable=False)
    mentor_username = db.Column(db.String, nullable=True)
    contributor_username = db.Column(db.String, nullable=True)
    title = db.Column(db.String, nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('dmp_orgs.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    repo_owner = db.Column(db.Text, nullable=True)
    repo = db.Column(db.String, nullable=True)
    
    
    # Relationship to Prupdates
    pr_updates = db.relationship('Prupdates', backref='pr_details', lazy=True)

    def __repr__(self):
        return f"<DmpIssue(id={self.id}, title={self.title})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_url': self.issue_url,
            'issue_number': self.issue_number,
            'mentor_username': self.mentor_username,
            'contributor_username': self.contributor_username,
            'title': self.title,
            'org_id': self.org_id,
            'description': self.description,
            'repo': self.repo
        }

class DmpIssueUpdate(db.Model):
    __tablename__ = 'dmp_issue_updates'

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    body_text = db.Column(db.Text, nullable=False)
    comment_link = db.Column(db.String, nullable=False)
    comment_id = db.Column(db.BigInteger, primary_key=True, nullable=False)
    comment_api = db.Column(db.String, nullable=False)
    comment_updated_at = db.Column(db.DateTime, nullable=False)
    dmp_id = db.Column(db.Integer, db.ForeignKey('dmp_orgs.id'), nullable=False)
    created_by = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<DmpIssueUpdate(comment_id={self.comment_id}, dmp_id={self.dmp_id})>"
    
    def to_dict(self):
        return {
            'created_at': self.created_at.isoformat(),
            'body_text': self.body_text,
            'comment_link': self.comment_link,
            'comment_id': self.comment_id,
            'comment_api': self.comment_api,
            'comment_updated_at': self.comment_updated_at.isoformat(),
            'dmp_id': self.dmp_id,
            'created_by': self.created_by
        }

class Prupdates(db.Model):
    __tablename__ = 'dmp_pr_updates'

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pr_id = db.Column(db.Integer, nullable=False,primary_key=True)
    status = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    pr_updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    merged_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    dmp_id = db.Column(db.Integer, db.ForeignKey('dmp_issues.id'), nullable=False)  # ForeignKey relationship
    link = db.Column(db.String, nullable=False)

    def __repr__(self):
            return f'<PullRequest {self.pr_id} - {self.title}>'

    def to_dict(self):
        return {
            'created_at': self.created_at.isoformat(),
            'pr_id': self.pr_id,
            'status': self.status,
            'title': self.title,
            'pr_updated_at': self.pr_updated_at.isoformat(),
            'merged_at': self.merged_at.isoformat() if self.merged_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'dmp_id': self.dmp_id,
            'link': self.link
        }

class DmpWeekUpdate(db.Model):
    __tablename__ = 'dmp_week_updates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    issue_url = db.Column(db.String, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    total_task = db.Column(db.Integer, nullable=False)
    completed_task = db.Column(db.Integer, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    task_data = db.Column(db.Text, nullable=False)
    dmp_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<DmpWeekUpdate(id={self.id}, week={self.week}, dmp_id={self.dmp_id})>"

# if __name__ == '__main__':
#     db.create_all()
