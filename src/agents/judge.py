"""
Judge Agent - Validates fixed code quality and tests
"""
import os
import sys
import json
import time
import google.generativeai as genai
from pathlib import Path
from src.prompts.system_prompts import JUDGE_SYSTEM_PROMPT

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.file_tools import read_file, run_pytest, run_pylint, get_file_info
from src.utils.logger import log_experiment, ActionType


# Load API key
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file!")

genai.configure(api_key=GOOGLE_API_KEY)


JUDGE_SYSTEM_PROMPT = """ROLE: Agent Testeur (Juge) Expert en Validation de Code

=== MISSION PRINCIPALE ===
Valider que le code corrigé est fonctionnel, sécurisé et de haute qualité.

=== CRITÈRES D'ÉVALUATION ===
1. FONCTIONNEMENT - Tous les tests unitaires passent
2. QUALITÉ - Score pylint > 8.0/10
3. SÉCURITÉ - Aucune vulnérabilité critique
4. DOCUMENTATION - Docstrings présents et complets
5. PERFORMANCE - Pas de régression significative

=== PROCESSUS DE VALIDATION ===
ÉTAPE 1: Exécution des tests
  - Lancer pytest sur le code corrigé
  - Vérifier que tous les tests passent
  - Analyser la couverture de code (si disponible)

ÉTAPE 2: Analyse de qualité
  - Exécuter pylint pour le score de qualité
  - Vérifier l'absence de nouvelles violations
  - Comparer avec le score précédent

ÉTAPE 3: Vérification de sécurité
  - Analyser le code pour les patterns dangereux
  - Vérifier les inputs non validés
  - Contrôler les dépendances risquées

ÉTAPE 4: Revue de documentation
  - Vérifier la présence de docstrings
  - Contrôler la qualité des commentaires
  - S'assurer de la clarté du code

=== DÉCISIONS POSSIBLES ===
1. PASS - Code valide, peut passer à la suite
2. FAIL - Problèmes critiques, besoin de re-correction
3. RETRY - Problèmes mineurs, une itération supplémentaire suffit

=== OUTILS DISPONIBLES ===
1. run_pytest(path) - Exécuter les tests unitaires
2. run_pylint(path) - Analyser la qualité du code
3. read_file(path) - Examiner le code source
4. get_code_metrics(path) - Vérifier les métriques

=== SEUILS DE DÉCISION ===
- PASS: Score pylint ≥ 8.0 ET tests à 100% ET pas de sécurité critique
- RETRY: Score pylint 7.0-7.9 OU tests < 100% OU problèmes mineurs
- FAIL: Score pylint < 7.0 OU tests échouent OU sécurité compromise

=== FORMAT DE SORTIE OBLIGATOIRE ===
{
  "verdict": "PASS|FAIL|RETRY",
  "test_results": {
    "total_tests": 10,
    "passed": 10,
    "failed": 0,
    "failure_details": ["liste des tests échoués"],
    "coverage_percentage": 95.5,
    "execution_time_seconds": 12.3
  },
  "quality_metrics": {
    "pylint_score": 9.2,
    "previous_score": 7.5,
    "improvement": 1.7,
    "new_issues": 0,
    "fixed_issues": 3,
    "remaining_issues": 2
  },
  "security_assessment": {
    "critical_issues": 0,
    "medium_issues": 1,
    "low_issues": 2,
    "recommendations": ["validation d'input manquante"]
  },
  "feedback": "Feedback constructif pour le Correcteur",
  "recommendations": [
    "Ajouter des tests pour les cas limites",
    "Améliorer la documentation de la fonction X"
  ],
  "next_action": "TERMINATE|CONTINUE_REFACTORING|FIX_TESTS"
}

=== NOTES IMPORTANTES ===
- Être objectif et basé sur des métriques
- Fournir un feedback constructif et actionnable
- Considérer le contexte du projet
- Ne pas être trop sévère sur les aspects cosmétiques
- Prioriser la fonctionnalité et la sécurité"""


class JudgeAgent:
    """
    Agent responsible for validating fixed code quality and tests
    """
    
    def __init__(self, model_name="gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        print(f"✅ Judge Agent initialized with model: {model_name}")
    
    def validate_file(self, file_path: str, test_file_path: str = None, previous_score: float = 0.0) -> dict:
        """
        Validate a fixed Python file
        
        Args:
            file_path: Path to the Python file to validate
            test_file_path: Optional path to test file for this code
            previous_score: Previous pylint score for comparison
            
        Returns:
            Dictionary containing validation verdict and metrics
        """
        print(f"\n⚖️  Judge validating: {file_path}")
        
        start_time = time.time()
        
        # Step 1: Read the fixed code
        fixed_code = read_file(file_path)
        if not fixed_code:
            print(f"❌ Could not read file: {file_path}")
            return {"error": "Could not read file", "verdict": "FAIL"}
        
        # Step 2: Run pylint analysis
        print("🔧 Running pylint analysis...")
        pylint_results = run_pylint(file_path)
        current_score = pylint_results.get('score', 0.0)
        total_issues = pylint_results.get('total_issues', 0)
        
        print(f"📊 Pylint score: {current_score}/10 (previous: {previous_score}/10)")
        print(f"⚠️  Issues found: {total_issues}")
        
        # Step 3: Run tests if test file provided
        test_results = None
        if test_file_path and os.path.exists(test_file_path):
            print(f"🧪 Running tests from {test_file_path}...")
            test_results = run_pytest(test_file_path)
            print(f"✅ Tests passed: {test_results.get('passed_count', 0)}")
            print(f"❌ Tests failed: {test_results.get('failed_count', 0)}")
        else:
            print("⚠️  No test file provided, skipping pytest")
            test_results = {
                "passed": None,
                "passed_count": 0,
                "failed_count": 0,
                "output": "No tests available"
            }
        
        # Step 4: Get file metrics
        file_info = get_file_info(file_path)
        
        # Step 5: Prepare prompt for LLM validation
        user_prompt = f"""Valide ce code Python corrigé et donne ton verdict.

**FICHIER:** {Path(file_path).name}
**LIGNES DE CODE:** {file_info.get('line_count', 0)}

**MÉTRIQUES PYLINT:**
- Score actuel: {current_score}/10
- Score précédent: {previous_score}/10
- Amélioration: {current_score - previous_score:.1f}
- Issues détectées: {total_issues}
- Détails: {json.dumps(pylint_results.get('issues', [])[:5], indent=2)}

**RÉSULTATS DES TESTS:**
{json.dumps(test_results, indent=2)}

**CODE CORRIGÉ:**
```python
{fixed_code}
```

**INSTRUCTIONS:**
Analyse le code selon les critères définis et retourne ton verdict en JSON.
Sois objectif, basé sur les métriques, et fournis un feedback constructif."""

        # Step 6: Call Gemini API for validation
        print("🤖 Calling Gemini API for validation...")
        try:
            response = self.model.generate_content(
                [
                    {"role": "user", "parts": [JUDGE_SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Je suis prêt à valider le code Python selon les critères définis. J'attends le code et les métriques à évaluer."]},
                    {"role": "user", "parts": [user_prompt]}
                ],
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 2000,
                }
            )
            
            raw_response = response.text.strip()
            print(f"✅ Received response from Gemini ({len(raw_response)} chars)")
            
            # Step 7: Parse JSON response
            # Clean markdown code blocks if present
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").replace("```", "").strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response.replace("```", "").strip()
            
            validation_result = json.loads(raw_response)
            
            # Step 8: Add actual metrics to result
            validation_result['actual_pylint_score'] = current_score
            validation_result['actual_test_passed'] = test_results.get('passed', None)
            validation_result['execution_time'] = time.time() - start_time
            
            # Step 9: Determine final verdict based on thresholds
            final_verdict = validation_result.get('verdict', 'FAIL')
            
            # Override verdict if metrics don't meet thresholds
            if current_score < 7.0:
                final_verdict = 'FAIL'
                validation_result['verdict_override'] = 'Score pylint trop bas'
            elif test_results.get('passed') is False:
                final_verdict = 'FAIL'
                validation_result['verdict_override'] = 'Tests échoués'
            elif current_score >= 8.0 and (test_results.get('passed') is True or test_results.get('passed') is None):
                final_verdict = 'PASS'
            
            validation_result['verdict'] = final_verdict
            
            # Step 10: Log the experiment
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Judge_Agent",
                model_used=self.model_name,
                action=ActionType.DEBUG,  # Judge is debugging/validating
                details={
                    "file_validated": file_path,
                    "test_file": test_file_path,
                    "pylint_score": current_score,
                    "previous_score": previous_score,
                    "total_issues": total_issues,
                    "tests_passed": test_results.get('passed'),
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "verdict": final_verdict,
                    "time_seconds": elapsed_time
                },
                status="SUCCESS"
            )
            
            print(f"⚖️  Final verdict: {final_verdict}")
            return validation_result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {raw_response[:500]}...")
            
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Judge_Agent",
                model_used=self.model_name,
                action=ActionType.DEBUG,
                details={
                    "file_validated": file_path,
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "error": f"JSON parse error: {str(e)}"
                },
                status="FAILED"
            )
            
            # Return a basic verdict based on metrics
            basic_verdict = "PASS" if current_score >= 8.0 and test_results.get('passed') != False else "FAIL"
            
            return {
                "verdict": basic_verdict,
                "error": "Failed to parse LLM response",
                "actual_pylint_score": current_score,
                "actual_test_passed": test_results.get('passed'),
                "raw_response": raw_response[:500]
            }
        
        except Exception as e:
            print(f"❌ Error during validation: {e}")
            
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Judge_Agent",
                model_used=self.model_name,
                action=ActionType.DEBUG,
                details={
                    "file_validated": file_path,
                    "input_prompt": user_prompt,
                    "output_response": "",
                    "error": str(e)
                },
                status="FAILED"
            )
            
            return {"error": str(e), "verdict": "FAIL"}


# Test the agent if run directly
if __name__ == "__main__":
    print("🧪 Testing Judge Agent...")
    
    # Create a test file with good code
    test_code = """
def calculate_average(numbers):
    '''Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers
        
    Returns:
        Average or 0.0 if empty
    '''
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)

def add_numbers(a, b):
    '''Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    '''
    return a + b
"""
    
    test_file = "test_good_code.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    # Test the agent
    judge = JudgeAgent()
    result = judge.validate_file(test_file, previous_score=6.5)
    
    print("\n" + "="*50)
    print("VALIDATION RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Clean up
    import os
    os.remove(test_file)