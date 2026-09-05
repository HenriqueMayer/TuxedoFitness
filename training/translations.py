"""Reviewed display-only terminology, bound to provider IDs during import.

Exact source titles prevent applying a translation to an unrelated movement.
Custom exercises and unknown names always retain their owner's original text.
"""
from django.utils.translation import get_language

CATALOG_VERSION = 'pt-br-2026-09-05'
REVIEWED_TITLES = {
    'Bench Press (Barbell)': 'Supino reto (barra)',
    'Bench Press (Dumbbell)': 'Supino reto (halteres)',
    'Bench Press (Smith Machine)': 'Supino reto (Smith)',
    'Incline Bench Press (Barbell)': 'Supino inclinado (barra)',
    'Incline Bench Press (Dumbbell)': 'Supino inclinado (halteres)',
    'Decline Bench Press (Barbell)': 'Supino declinado (barra)',
    'Chest Press (Machine)': 'Supino (máquina)',
    'Chest Fly (Dumbbell)': 'Crucifixo (halteres)',
    'Chest Fly (Machine)': 'Crucifixo (máquina)',
    'Cable Fly Crossovers': 'Crucifixo cruzado (cabos)',
    'Push Up': 'Flexão de braços',
    'Squat (Barbell)': 'Agachamento (barra)',
    'Squat (Dumbbell)': 'Agachamento (halteres)',
    'Squat (Smith Machine)': 'Agachamento (Smith)',
    'Front Squat': 'Agachamento frontal',
    'Goblet Squat': 'Agachamento goblet',
    'Hack Squat (Machine)': 'Agachamento hack (máquina)',
    'Leg Press (Machine)': 'Leg press (máquina)',
    'Leg Extension (Machine)': 'Cadeira extensora',
    'Seated Leg Curl (Machine)': 'Cadeira flexora',
    'Lying Leg Curl (Machine)': 'Mesa flexora',
    'Standing Calf Raise': 'Elevação de panturrilhas em pé',
    'Seated Calf Raise': 'Elevação de panturrilhas sentado',
    'Deadlift (Barbell)': 'Levantamento terra (barra)',
    'Romanian Deadlift (Barbell)': 'Levantamento terra romeno (barra)',
    'Romanian Deadlift (Dumbbell)': 'Levantamento terra romeno (halteres)',
    'Sumo Deadlift': 'Levantamento terra sumô',
    'Hip Thrust (Barbell)': 'Elevação pélvica (barra)',
    'Hip Thrust (Machine)': 'Elevação pélvica (máquina)',
    'Bulgarian Split Squat': 'Agachamento búlgaro',
    'Lunge (Dumbbell)': 'Afundo (halteres)',
    'Walking Lunge (Dumbbell)': 'Afundo com caminhada (halteres)',
    'Hip Abduction (Machine)': 'Cadeira abdutora',
    'Hip Adduction (Machine)': 'Cadeira adutora',
    'Pull Up': 'Barra fixa',
    'Chin Up': 'Barra fixa com pegada supinada',
    'Assisted Pull Up': 'Barra fixa assistida',
    'Lat Pulldown (Cable)': 'Puxada alta (cabo)',
    'Lat Pulldown (Machine)': 'Puxada alta (máquina)',
    'Seated Cable Row - V Grip (Cable)': 'Remada baixa com triângulo (cabo)',
    'Bent Over Row (Barbell)': 'Remada curvada (barra)',
    'Bent Over Row (Dumbbell)': 'Remada curvada (halteres)',
    'Dumbbell Row': 'Remada (halter)',
    'T Bar Row': 'Remada cavalinho',
    'Face Pull': 'Puxada à face',
    'Shrug (Dumbbell)': 'Encolhimento de ombros (halteres)',
    'Shrug (Barbell)': 'Encolhimento de ombros (barra)',
    'Overhead Press (Barbell)': 'Desenvolvimento acima da cabeça (barra)',
    'Shoulder Press (Dumbbell)': 'Desenvolvimento de ombros (halteres)',
    'Shoulder Press (Machine)': 'Desenvolvimento de ombros (máquina)',
    'Arnold Press (Dumbbell)': 'Desenvolvimento Arnold (halteres)',
    'Lateral Raise (Dumbbell)': 'Elevação lateral (halteres)',
    'Lateral Raise (Cable)': 'Elevação lateral (cabo)',
    'Front Raise (Dumbbell)': 'Elevação frontal (halteres)',
    'Reverse Fly (Machine)': 'Crucifixo inverso (máquina)',
    'Bicep Curl (Barbell)': 'Rosca bíceps (barra)',
    'Bicep Curl (Dumbbell)': 'Rosca bíceps (halteres)',
    'Bicep Curl (Cable)': 'Rosca bíceps (cabo)',
    'Hammer Curl (Dumbbell)': 'Rosca martelo (halteres)',
    'Preacher Curl (Barbell)': 'Rosca Scott (barra)',
    'Concentration Curl': 'Rosca concentrada',
    'Triceps Pushdown': 'Tríceps na polia',
    'Triceps Rope Pushdown': 'Tríceps na polia com corda',
    'Triceps Extension (Dumbbell)': 'Extensão de tríceps (halteres)',
    'Skullcrusher (Barbell)': 'Tríceps testa (barra)',
    'Triceps Dip': 'Mergulho para tríceps',
    'Plank': 'Prancha',
    'Side Plank': 'Prancha lateral',
    'Crunch': 'Abdominal',
    'Crunch (Machine)': 'Abdominal (máquina)',
    'Hanging Leg Raise': 'Elevação de pernas suspenso',
    'Cable Crunch': 'Abdominal na polia',
    'Russian Twist': 'Rotação russa',
    'Running': 'Corrida',
    'Walking': 'Caminhada',
    'Cycling': 'Ciclismo',
    'Treadmill': 'Esteira',
    'Elliptical Trainer': 'Elíptico',
    'Stair Machine (Floors)': 'Escada (andares)',
    'Rowing Machine': 'Remo ergométrico',
    'Swimming': 'Natação',
}


def translated_title(title, is_custom=False):
    return '' if is_custom else REVIEWED_TITLES.get(title, '')


def display_name(exercise):
    if get_language() == 'pt-br' and not exercise.is_custom:
        return exercise.title_pt_br or exercise.title
    return exercise.title
