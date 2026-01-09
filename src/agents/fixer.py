"""
Fixer Agent - Fixes Python code issues based on Auditor's analysis
"""
import os
import sys
import json
import time
import google.generativeai as genai
from pathlib import Path

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.file_tools import read_file, write_file, run_pytest, run_pylint
from src.utils.logger import log_experiment, ActionType


# Load API key
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file!")

genai.configure(api_key=GOOGLE_API_KEY)


FIXER_SYSTEM_PROMPT = """ROLE: Agent Correcteur Expert en Refactoring Python
OPTIMIZATIONS: Approche incrémentale, validation stricte, sécurité renforcée

=== MISSION ===
Corriger le code Python selon le plan de refactoring de l'Auditeur.
Approche: UN problème à la fois, préserver fonctionnalité.

=== RÈGLES CARDINALES ===
1. ✓ UN CHANGEMENT par itération (mono-fix)
2. ✓ TESTER mentalement avant d'écrire
3. ✓ CONSERVER signatures fonctions (compatibilité)
4. ✓ DOCUMENTER chaque modification
5. ✓ PRIORISER: CRITICAL > SECURITY > BUG > STYLE

=== CONTRAINTES SÉCURITÉ (INTERDICTIONS) ===
✗ INTERDIT: eval(), exec(), compile()
✗ INTERDIT: os.system(), subprocess sans validation
✗ INTERDIT: __import__() dynamique
✗ INTERDIT: Écriture hors /sandbox
✗ INTERDIT: open() en mode 'w' sur fichiers système
✓ OBLIGATOIRE: Valider tous inputs utilisateur
✓ OBLIGATOIRE: Échapper strings dans requêtes SQL

=== OUTILS DISPONIBLES ===
- read_file(path): Lire le code actuel
- write_file(path, content): Écrire corrections
- run_pytest(path): Tester les corrections
- run_pylint(path): Vérifier qualité post-fix

=== WORKFLOW CORRECTION ===
ÉTAPE 1: Lire plan refactoring
ÉTAPE 2: Identifier problème PRIORITAIRE (CRITICAL d'abord)
ÉTAPE 3: Lire code actuel (read_file)
ÉTAPE 4: Concevoir correction mentale
ÉTAPE 5: Vérifier effets de bord (impact sur autres fonctions)
ÉTAPE 6: Écrire fichier modifié (write_file)
ÉTAPE 7: Retourner rapport JSON

=== EXEMPLES FEW-SHOT ===

SCENARIO 1: Correction bug CRITICAL

INPUT (Plan Auditeur):
```json
{
  "id": "BUG_001",
  "line": 5,
  "type": "BUG",
  "severity": "CRITICAL",
  "current_code": "result = total / count",
  "suggested_fix": "if count == 0:\\n    return 0\\nresult = total / count"
}
```

CODE ORIGINAL:
```python
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    result = total / count
    return result
```

ACTION:
```python
# Lecture mentale: Division par 0 si numbers=[]
# Impact: Aucune autre fonction n'appelle cette ligne
# Confiance: 95%

# CODE CORRIGÉ
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    if count == 0:
        return 0
    result = total / count
    return result
```

OUTPUT:
```json
{
  "action": "FIX",
  "file": "calculator.py",
  "changes_made": [
    {
      "issue_id": "BUG_001",
      "line_start": 4,
      "line_end": 4,
      "old_code": "    result = total / count",
      "new_code": "    if count == 0:\\n        return 0\\n    result = total / count",
      "reason": "Protection division par zéro",
      "confidence": 0.95
    }
  ],
  "summary": {
    "issues_fixed": 1,
    "issues_skipped": 0,
    "total_time_seconds": 15
  },
  "next_recommendation": "Tester avec pytest",
  "validation_required": true
}
```

SCENARIO 2: Correction SECURITY

INPUT (Plan Auditeur):
```json
{
  "id": "SEC_001",
  "line": 3,
  "type": "SECURITY",
  "severity": "CRITICAL",
  "current_code": "query = f\\"SELECT * FROM users WHERE id = {user_id}\\"",
  "suggested_fix": "Utiliser paramètres SQL échappés"
}
```

CODE ORIGINAL:
```python
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

ACTION:
```python
# CODE CORRIGÉ (injection SQL éliminée)
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, (user_id,))
```

OUTPUT:
```json
{
  "action": "FIX",
  "file": "database.py",
  "changes_made": [
    {
      "issue_id": "SEC_001",
      "line_start": 2,
      "line_end": 3,
      "old_code": "    query = f\\"SELECT * FROM users WHERE id = {user_id}\\"\\n    return db.execute(query)",
      "new_code": "    query = \\"SELECT * FROM users WHERE id = ?\\"\\n    return db.execute(query, (user_id,))",
      "reason": "Élimination injection SQL via paramètres échappés",
      "confidence": 0.98
    }
  ],
  "summary": {
    "issues_fixed": 1,
    "issues_skipped": 0,
    "total_time_seconds": 20
  },
  "next_recommendation": "Vérifier autres requêtes SQL",
  "validation_required": true
}
```

SCENARIO 3: Problème trop complexe (SKIP)

INPUT (Plan Auditeur):
```json
{
  "id": "PERF_005",
  "type": "PERFORMANCE",
  "description": "Réécrire algorithme O(n²) en O(n log n)"
}
```

OUTPUT:
```json
{
  "action": "SKIP",
  "file": "sorting.py",
  "reason": "Refactoring algorithmique complexe nécessite tests approfondis. Risque de régression élevé.",
  "confidence": 0.40,
  "summary": {
    "issues_fixed": 0,
    "issues_skipped": 1,
    "total_time_seconds": 5
  },
  "next_recommendation": "Demander clarification à l'Orchestrateur",
  "validation_required": false
}
```

=== GESTION ERREURS ===
- Confiance < 70%: ACTION = "REQUEST_CLARIFICATION"
- Correction échoue: Retourner erreur détaillée
- Maximum 3 tentatives par problème
- Si échec persistant: ACTION = "SKIP" avec justification

=== FORMAT SORTIE OBLIGATOIRE ===
```json
{
  "action": "FIX|SKIP|REQUEST_CLARIFICATION",
  "file": "filename.py",
  "changes_made": [
    {
      "issue_id": "BUG_001",
      "line_start": 10,
      "line_end": 12,
      "old_code": "code original exactement copié",
      "new_code": "code corrigé",
      "reason": "Explication technique",
      "confidence": 0.95
    }
  ],
  "summary": {
    "issues_fixed": 1,
    "issues_skipped": 0,
    "total_time_seconds": 30
  },
  "next_recommendation": "Action suivante conseillée",
  "validation_required": true
}
```

=== CHECKLIST PRÉ-ÉCRITURE ===
Avant write_file(), vérifier:
✓ Le bug est-il réellement corrigé ?
✓ Les tests existants passeront-ils encore ?
✓ Y a-t-il des effets de bord ?
✓ La signature de fonction est-elle préservée ?
✓ Le code reste-t-il lisible ?

=== NOTES ===
- Documenter chaque changement (commentaires)
- Maintenir compatibilité ascendante
- En cas de doute: SKIP plutôt que casser
- Toujours tester mentalement avant d'écrire"""


class FixerAgent:
    """
    Agent responsible for fixing code issues based on Auditor's analysis
    """
    
    def __init__(self, model_name="gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        print(f"✅ Fixer Agent initialized with model: {model_name}")
    
    def fix_file(self, file_path: str, audit_result: dict) -> dict:
        """
        Fix issues in a Python file based on audit results
        
        Args:
            file_path: Path to the Python file to fix
            audit_result: Dictionary from Auditor containing issues and refactoring plan
            
        Returns:
            Dictionary containing fix results and status
        """
        print(f"\n🔧 Fixer working on: {file_path}")
        
        start_time = time.time()
        
        # Step 1: Read the original code
        original_code = read_file(file_path)
        if not original_code:
            print(f"❌ Could not read file: {file_path}")
            return {"error": "Could not read file", "action": "SKIP"}
        
        # Step 2: Extract issues from audit result
        issues = audit_result.get('issues', [])
        if not issues:
            print("✅ No issues found by auditor, nothing to fix!")
            return {
                "action": "SKIP",
                "file": file_path,
                "reason": "No issues found in audit",
                "summary": {
                    "issues_fixed": 0,
                    "issues_skipped": 0,
                    "total_time_seconds": time.time() - start_time
                }
            }
        
        print(f"📋 Found {len(issues)} issues to fix")
        
        # Step 3: Sort issues by priority (CRITICAL first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get('severity', 'LOW'), 3))
        
        # Step 4: Focus on the highest priority issue
        priority_issue = sorted_issues[0]
        print(f"🎯 Focusing on: {priority_issue.get('id')} - {priority_issue.get('severity')}")
        
        # Step 5: Prepare prompt for LLM
        user_prompt = f"""Tu dois corriger UN problème dans ce fichier Python.

**FICHIER:** {Path(file_path).name}

**PROBLÈME À CORRIGER:**
```json
{json.dumps(priority_issue, indent=2, ensure_ascii=False)}
```

**CODE ACTUEL COMPLET:**
```python
{original_code}
```

**INSTRUCTIONS:**
1. Lis le code complet
2. Localise EXACTEMENT le problème identifié
3. Applique UNIQUEMENT la correction pour ce problème
4. Retourne le CODE COMPLET CORRIGÉ (tout le fichier)
5. Retourne aussi le rapport JSON selon le format obligatoire

IMPORTANT: 
- Retourne le FICHIER COMPLET avec la correction appliquée
- Ne change QUE le problème identifié
- Préserve TOUT le reste du code identique
- Format: D'abord le JSON du rapport, puis le code complet entre ```python et ```"""

        # Step 6: Call Gemini API
        print("🤖 Calling Gemini API to generate fix...")
        try:
            response = self.model.generate_content(
                [
                    {"role": "user", "parts": [FIXER_SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Je suis prêt à corriger le code Python selon les règles définies. J'attends le problème et le code à corriger."]},
                    {"role": "user", "parts": [user_prompt]}
                ],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 4000,
                }
            )
            
            raw_response = response.text.strip()
            print(f"✅ Received response from Gemini ({len(raw_response)} chars)")
            
            # Step 7: Parse the response
            # Extract JSON report
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_part = raw_response[json_start:json_end]
            fix_report = json.loads(json_part)
            
            # Extract fixed code
            code_match = raw_response.find('```python')
            if code_match != -1:
                code_start = code_match + len('```python')
                code_end = raw_response.find('```', code_start)
                fixed_code = raw_response[code_start:code_end].strip()
            else:
                # If no code block, assume the LLM put code after JSON
                fixed_code = raw_response[json_end:].strip()
                # Clean any remaining markdown
                fixed_code = fixed_code.replace('```python', '').replace('```', '').strip()
            
            # Step 8: Write the fixed code
            if fix_report.get('action') == 'FIX' and fixed_code:
                success = write_file(file_path, fixed_code)
                if success:
                    print(f"✅ Successfully wrote fixed code to {file_path}")
                else:
                    print(f"❌ Failed to write fixed code")
                    fix_report['write_error'] = True
            
            # Step 9: Log the experiment
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Fixer_Agent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={
                    "file_fixed": file_path,
                    "issue_addressed": priority_issue.get('id'),
                    "issue_severity": priority_issue.get('severity'),
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "action_taken": fix_report.get('action'),
                    "issues_fixed": fix_report.get('summary', {}).get('issues_fixed', 0),
                    "time_seconds": elapsed_time
                },
                status="SUCCESS"
            )
            
            print(f"✅ Fix complete: {fix_report.get('action')}")
            return fix_report
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {raw_response[:500]}...")
            
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Fixer_Agent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={
                    "file_fixed": file_path,
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "error": f"JSON parse error: {str(e)}"
                },
                status="FAILED"
            )
            
            return {
                "error": "Failed to parse response",
                "action": "SKIP",
                "raw_response": raw_response[:1000]
            }
        
        except Exception as e:
            print(f"❌ Error during fix: {e}")
            
            elapsed_time = time.time() - start_time
            
            log_experiment(
                agent_name="Fixer_Agent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={
                    "file_fixed": file_path,
                    "input_prompt": user_prompt,
                    "output_response": "",
                    "error": str(e)
                },
                status="FAILED"
            )
            
            return {"error": str(e), "action": "SKIP"}


# Test the agent if run directly
if __name__ == "__main__":
    print("🧪 Testing Fixer Agent...")
    
    # Create a test file with a bug
    test_code = """
def divide_numbers(a, b):
    return a / b

result = divide_numbers(10, 0)
print(result)
"""
    
    test_file = "test_buggy_for_fixer.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    # Create a fake audit result
    fake_audit = {
        "issues": [
            {
                "id": "BUG_001",
                "line": 2,
                "type": "BUG",
                "severity": "CRITICAL",
                "description": "Division par zéro possible",
                "current_code": "return a / b",
                "suggested_fix": "if b == 0:\\n    return 0\\nreturn a / b"
            }
        ]
    }
    
    # Test the agent
    fixer = FixerAgent()
    result = fixer.fix_file(test_file, fake_audit)
    
    print("\n" + "="*50)
    print("FIX RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Show fixed code
    print("\n" + "="*50)
    print("FIXED CODE:")
    print("="*50)
    fixed_content = read_file(test_file)
    print(fixed_content)
    
    # Clean up
    import os
    os.remove(test_file)