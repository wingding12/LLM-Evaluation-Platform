from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from datetime import timedelta
from api_clients import model_functions
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv(dotenv_path='.env')

app = Flask(__name__, template_folder='frontend/templates')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models
class Experiment(db.Model):
    __tablename__ = 'experiments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Model(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiments.id', ondelete='CASCADE'))
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'))
    test_case = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=True)
    response_text = db.Column(db.Text, nullable=False)
    response_time = db.Column(db.Interval, nullable=False)
    factuality_score = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

@app.route('/')
def index():
    models = Model.query.all()
    return render_template('index.html', models=models)

@app.route('/evaluate_test_cases', methods=['POST'])
def evaluate_test_cases():
    data = request.json
    test_cases = data.get('test_cases')
    selected_models = data.get('selected_models')
    system_prompt = data.get('system_prompt')

    responses = []
    for test_case_data in test_cases:
        test_case_prompt = test_case_data['testCase']
        expected_output = test_case_data['expectedOutput']

        combined_prompt = f"{system_prompt}\n\nUser: {test_case_prompt}"

        response_data = {
            'test_case': test_case_prompt,
            'expected_output': expected_output
        }

        for model_name in selected_models:
            try:
                import time
                start_time = time.time()
                
                model_func = model_functions(model_name)
                result = model_func(combined_prompt, expected_output)
                
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                response_data[model_name] = result['response']
                response_data[f"{model_name}_response_time"] = f"{response_time}s"
            except Exception as e:
                response_data[model_name] = f"Error generating response: {str(e)}"
                response_data[f"{model_name}_response_time"] = "N/A"

        responses.append(response_data)

    return jsonify({'responses': responses})

def evaluate_factuality(response, expected_output):
    # Use cosine similarity to evaluate the factual closeness of the response to the expected output
    vectorizer = CountVectorizer().fit_transform([response, expected_output])
    vectors = vectorizer.toarray()
    cosine_sim = cosine_similarity(vectors)
    score = cosine_sim[0][1]  # Similarity between the response and expected output
    return f"Cosine Similarity: {score:.2f}"

@app.route('/experiments')
def experiments():
    experiments = Experiment.query.order_by(Experiment.created_at.desc()).all()
    return render_template('experiments.html', experiments=experiments)

@app.route('/submit_prompt', methods=['POST'])
def submit_prompt():
    try:
        experiment_name = request.form.get('experiment_name')
        system_prompt = request.form.get('system_prompt')
        selected_models = request.form.getlist('selected_models')
        experiment_id = request.form.get('experiment_id')

        if experiment_id:
            # Update existing experiment
            experiment = Experiment.query.get_or_404(experiment_id)
            experiment.name = experiment_name
            experiment.system_prompt = system_prompt
            db.session.commit()

            # Get all unique test cases for this experiment
            responses = Response.query.filter_by(experiment_id=experiment_id).all()
            
            # Group responses by test case
            test_cases = {}
            for response in responses:
                if response.test_case not in test_cases:
                    test_cases[response.test_case] = {
                        'test_case': response.test_case,
                        'expected_output': response.expected_output
                    }
                
                # Get the model name for this response
                model = Model.query.get(response.model_id)
                if model:
                    test_cases[response.test_case][model.name] = {
                        'response': response.response_text,
                        'factuality_score': response.factuality_score
                    }

            return jsonify({
                'message': 'Experiment updated successfully',
                'experiment_id': experiment.id,
                'existing_responses': list(test_cases.values()),
                'selected_models': selected_models,
                'is_existing': True
            })
        else:
            # Create new experiment
            new_experiment = Experiment(
                name=experiment_name,
                system_prompt=system_prompt
            )
            db.session.add(new_experiment)
            db.session.commit()

            return jsonify({
                'message': 'Experiment created successfully',
                'experiment_id': new_experiment.id,
                'existing_responses': [],
                'selected_models': selected_models,
                'is_existing': False
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    db.session.query(Experiment).delete()
    db.session.commit()
    return redirect(url_for('experiments'))

@app.route('/continue_experiment/<int:experiment_id>', methods=['GET', 'POST'])
def continue_experiment(experiment_id):
    original_experiment = Experiment.query.get_or_404(experiment_id)
    models = Model.query.all()

    if request.method == 'POST':
        # Get updated details from the form
        new_name = request.form['experiment_name']
        new_prompt = request.form['system_prompt']

        # Create a new experiment with the updated details
        new_experiment = Experiment(name=new_name, system_prompt=new_prompt)
        db.session.add(new_experiment)
        db.session.commit()

        # Copy responses from the original experiment to the new one
        original_responses = Response.query.filter_by(experiment_id=experiment_id).all()
        for response in original_responses:
            new_response = Response(
                experiment_id=new_experiment.id,
                model_id=response.model_id,
                response_text=response.response_text,
                response_time=response.response_time,
                factuality_score=response.factuality_score
            )
            db.session.add(new_response)

        # Delete the original experiment
        db.session.delete(original_experiment)
        db.session.commit()

        return redirect(url_for('experiments'))

    return render_template('index.html', experiment=original_experiment, models=models)

@app.route('/delete_experiment/<int:experiment_id>', methods=['POST'])
def delete_experiment(experiment_id):
    experiment = Experiment.query.get_or_404(experiment_id)
    db.session.delete(experiment)
    db.session.commit()
    return redirect(url_for('experiments'))

@app.route('/submit_test_case', methods=['POST'])
def submit_test_case():
    try:
        data = request.json
        experiment_id = data.get('experiment_id')
        test_case_prompt = data.get('test_case_prompt')
        expected_output = data.get('expected_output')
        selected_models = data.get('selected_models', [])

        # Ensure the experiment exists
        experiment = Experiment.query.get_or_404(experiment_id)
        
        # Get system prompt from experiment
        system_prompt = experiment.system_prompt
        combined_prompt = f"{system_prompt}\n\n{test_case_prompt}"

        responses = []
        # Create responses for each selected model
        for model_name in selected_models:
            model = Model.query.filter_by(name=model_name).first()
            if model:
                # Get model response
                response_text = model_functions(model_name)(combined_prompt)
                response_time = timedelta(seconds=1)  # Simulated response time
                factuality_score = evaluate_factuality(response_text, expected_output)

                # Save response to database
                new_response = Response(
                    experiment_id=experiment_id,
                    model_id=model.id,
                    test_case=test_case_prompt,
                    expected_output=expected_output,
                    response_text=response_text,
                    response_time=response_time,
                    factuality_score=factuality_score
                )
                db.session.add(new_response)
                
                # Add to responses list
                responses.append({
                    'model': model_name,
                    'response': response_text,
                    'factuality_score': factuality_score
                })

        db.session.commit()
        return jsonify({
            'message': 'Test case submitted successfully',
            'responses': responses
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/experiment/<int:experiment_id>')
def get_experiment(experiment_id):
    try:
        experiment = Experiment.query.get_or_404(experiment_id)
        
        # Get all responses for this experiment
        responses = Response.query.filter_by(experiment_id=experiment_id).all()
        
        # Get unique models used in this experiment
        used_models = set()
        for response in responses:
            model = Model.query.get(response.model_id)
            if model:
                used_models.add(model.name)

        # Group responses by test case
        test_cases = {}
        for response in responses:
            if response.test_case not in test_cases:
                test_cases[response.test_case] = {
                    'test_case': response.test_case,
                    'expected_output': response.expected_output
                }
            
            model = Model.query.get(response.model_id)
            if model:
                test_cases[response.test_case][model.name] = {
                    'response': response.response_text,
                    'factuality_score': response.factuality_score
                }

        return jsonify({
            'experiment': {
                'id': experiment.id,
                'name': experiment.name,
                'system_prompt': experiment.system_prompt,
                'selected_models': list(used_models)
            },
            'responses': list(test_cases.values())
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        model_names = ["GPT", "Gemini", "Llama", "Mistral"]
        for name in model_names:
            if not Model.query.filter_by(name=name).first():
                db.session.add(Model(name=name))
        db.session.commit()

    app.run(debug=True)