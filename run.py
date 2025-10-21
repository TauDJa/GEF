# run.py
from app import create_app, db
from app.models import Gef, Personnel, Wilaya, Commune, Telephone, Agrement, TypeEquipement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'app': app, 
        'db': db, 
        'Gef': Gef, 
        'Personnel': Personnel,
        'Wilaya': Wilaya,
        'Commune': Commune,
        'Telephone': Telephone,
        'Agrement': Agrement,
        'TypeEquipement': TypeEquipement
    }

if __name__ == '__main__':
    app.run()