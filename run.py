from app import create_app, db
from app.models import User, Room, Client, Booking

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Room': Room,
        'Client': Client,
        'Booking': Booking
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            user = User(username='admin', 
                       email='admin@example.com',
                       role='supervisor')
            user.password = 'admin123'
            db.session.add(user)
            db.session.commit()
    app.run(debug=True)
