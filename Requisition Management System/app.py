# app.py
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///requisitions.db' # Using SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Model ---
class Requisition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    justification = db.Column(db.Text, nullable=False)
    requester_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Pending Approval') # e.g., Pending Approval, Approved, Rejected, Fulfilled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'justification': self.justification,
            'requester_name': self.requester_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }

# --- Database Initialization (Run once to create the database) ---
@app.before_first_request
def create_tables():
    db.create_all()

# --- API Endpoints ---

@app.route('/')
def index():
    """Renders the main HTML page for the frontend."""
    return render_template('index.html')

@app.route('/api/requisitions', methods=['POST'])
def create_requisition():
    """API endpoint to create a new requisition."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    new_requisition = Requisition(
        item_name=data.get('item_name'),
        quantity=data.get('quantity'),
        justification=data.get('justification'),
        requester_name=data.get('requester_name')
    )
    if not all([new_requisition.item_name, new_requisition.quantity,
                new_requisition.justification, new_requisition.requester_name]):
        return jsonify({"error": "Missing required fields"}), 400

    db.session.add(new_requisition)
    db.session.commit()
    return jsonify(new_requisition.to_dict()), 201

@app.route('/api/requisitions', methods=['GET'])
def get_all_requisitions():
    """API endpoint to get all requisitions."""
    requisitions = Requisition.query.all()
    return jsonify([req.to_dict() for req in requisitions])

@app.route('/api/requisitions/<int:req_id>/approve', methods=['POST'])
def approve_requisition(req_id):
    """API endpoint to approve a requisition."""
    # In a real system, you'd add authentication/authorization here
    # to ensure only authorized approvers can do this.

    requisition = Requisition.query.get_or_404(req_id)
    data = request.get_json()
    approver_name = data.get('approver_name', 'System Approver') # Default for example

    if requisition.status == 'Pending Approval':
        requisition.status = 'Approved'
        requisition.approved_by = approver_name
        requisition.approved_at = datetime.utcnow()
        db.session.commit()
        return jsonify(requisition.to_dict()), 200
    else:
        return jsonify({"message": f"Requisition is already {requisition.status}"}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Ensure tables are created when the app starts if they don't exist
    app.run(debug=True) # debug=True is for development, set to False for production