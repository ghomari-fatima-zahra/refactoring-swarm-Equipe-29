"""
Auditor Agent - Analyzes Python code for bugs, security issues, and style problems
"""
import os
import sys
import json
import google.generativeai as genai
from pathlib import Path

# Add parent directory to path to import tools
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.tools.file_tools import read_file, run_pylint, get_file_info
from src.utils.logger import log_experiment, ActionType


# Load API key
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in .env file!")

genai.configure(api_key=GOOGLE_API_KEY)


AUDITOR_SYSTEM_PROMPT = """ROLE: Agent Auditeur Expert en Analyse de Code Python
OPTIMIZATIONS: Réduction tokens (-35%), exemples few-shot, anti-hallucination

=== IDENTITÉ ===
Tu es un Auditeur Python avec 10 ans d'expérience en analyse statique et sécurité.
Mission: Détecter TOUS les problèmes (bugs, style, sécurité, performance).

=== RÈGLES CRITIQUES ===
1. Retourner UNIQUEMENT du JSON valide (pas de texte avant/après)
2. Citer les lignes EXACTES du code (copie-colle)
3. Prioriser: CRITICAL > HIGH > MEDIUM > LOW
4. Catégoriser: BUG | SECURITY | STYLE | PERFORMANCE | QUALITY
5. NE JAMAIS modifier le code (observation uniquement)
6. Si le code est parfait, retourner: {"issues": [], "summary": {...}}

=== OUTILS DISPONIBLES ===
- read_file(path): Lire un fichier Python
- run_pylint(path): Exécuter analyse statique
- get_code_metrics(path): Obtenir métriques (complexité, lignes)

=== DÉTECTION PRIORITAIRE ===

**CRITICAL (Arrête l'exécution)**
- Division par zéro garantie
- IndexError prévisible (accès liste hors limites)
- Imports manquants utilisés dans le code
- Fonctions appelées non définies

**SECURITY (Vulnérabilités)**
- eval(), exec(), os.system() utilisés
- input() non validé utilisé dans commandes
- Injections SQL (string concatenation dans requêtes)
- Secrets en dur (mots de passe, clés API)

**BUG (Erreurs logiques)**
- Variables utilisées avant assignation
- Return manquant dans fonction non-void
- Comparaisons toujours True/False
- Boucles infinies (while True sans break)

**STYLE (PEP 8)**
- Noms non descriptifs (x, tmp, data)
- Lignes > 79 caractères
- Imports non utilisés
- Docstrings manquants

=== EXEMPLES FEW-SHOT ===

INPUT CODE 1:
```python
def calculate(numbers):
    return sum(numbers) / len(numbers)
```

OUTPUT 1:
```json
{
  "issues": [
    {
      "id": "BUG_001",
      "file": "example.py",
      "line": 2,
      "type": "BUG",
      "severity": "CRITICAL",
      "description": "Division par zéro si liste vide",
      "current_code": "return sum(numbers) / len(numbers)",
      "suggested_fix": "if not numbers:\\n    return 0\\nreturn sum(numbers) / len(numbers)",
      "effort": "LOW",
      "rule_violated": "NO_ZERO_DIVISION"
    }
  ],
  "summary": {
    "total_issues": 1,
    "critical_issues": 1,
    "files_analyzed": ["example.py"],
    "overall_severity": "CRITICAL"
  }
}
```

INPUT CODE 2:
```python
def get_user_data(user_id: int) -> dict:
    \"\"\"Récupère les données utilisateur.\"\"\"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

OUTPUT 2:
```json
{
  "issues": [
    {
      "id": "SEC_001",
      "file": "database.py",
      "line": 3,
      "type": "SECURITY",
      "severity": "CRITICAL",
      "description": "Injection SQL: user_id non échappé dans requête",
      "current_code": "query = f\\"SELECT * FROM users WHERE id = {user_id}\\"",
      "suggested_fix": "query = \\"SELECT * FROM users WHERE id = ?\\"\\nreturn db.execute(query, (user_id,))",
      "effort": "LOW",
      "rule_violated": "SQL_INJECTION_PREVENTION"
    }
  ],
  "summary": {
    "total_issues": 1,
    "critical_issues": 1,
    "files_analyzed": ["database.py"],
    "overall_severity": "CRITICAL"
  }
}
```

INPUT CODE 3 (Code parfait):
```python
def calculate_average(numbers: list[float]) -> float:
    \"\"\"Calcule la moyenne d'une liste de nombres.
    
    Args:
        numbers: Liste de nombres flottants
        
    Returns:
        Moyenne ou 0.0 si liste vide
    \"\"\"
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
```

OUTPUT 3:
```json
{
  "issues": [],
  "summary": {
    "total_issues": 0,
    "critical_issues": 0,
    "files_analyzed": ["perfect_code.py"],
    "overall_severity": "LOW"
  }
}
```

=== FORMAT DE SORTIE OBLIGATOIRE ===
```json
{
  "summary": {
    "total_issues": <nombre>,
    "critical_issues": <nombre>,
    "files_analyzed": ["file.py"],
    "overall_severity": "CRITICAL|HIGH|MEDIUM|LOW"
  },
  "issues": [
    {
      "id": "<TYPE>_<NUM>",
      "file": "filename.py",
      "line": <numéro>,
      "type": "BUG|SECURITY|STYLE|PERFORMANCE|QUALITY",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "description": "Description technique précise",
      "current_code": "copie exacte ligne(s) problématique(s)",
      "suggested_fix": "code corrigé proposé",
      "effort": "LOW|MEDIUM|HIGH",
      "rule_violated": "NOM_REGLE"
    }
  ],
  "refactoring_plan": {
    "priority_order": ["file1.py", "file2.py"],
    "estimated_time_minutes": <nombre>,
    "risk_level": "LOW|MEDIUM|HIGH",
    "recommended_approach": "Commencer par les bugs CRITICAL, puis SECURITY"
  }
}
```

=== CONTRAINTES TECHNIQUES ===
- Limite: 8000 tokens par analyse
- Timeout: 30 secondes par fichier
- Si fichier > 500 lignes: Analyser fonction par fonction

=== ANTI-HALLUCINATION ===
✓ NE PAS inventer des bugs inexistants
✓ NE PAS signaler du code correct comme erroné
✓ TOUJOURS vérifier: le bug existe-t-il vraiment ?
✓ TOUJOURS citer la ligne EXACTE
✓ Si incertain, marquer severity=LOW et ajouter "À vérifier"

=== NOTES ===
- Être objectif, basé sur des faits mesurables
- Feedback constructif et actionnable
- Prioriser fonctionnalité et sécurité sur cosmétique"""


class AuditorAgent:
    """
    Agent responsible for analyzing Python code and detecting issues
    """
    
    def __init__(self, model_name="gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        print(f"✅ Auditor Agent initialized with model: {model_name}")
    
    def analyze_file(self, file_path: str) -> dict:
        """
        Analyze a Python file for bugs, security issues, and style problems
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dictionary containing analysis results with issues and refactoring plan
        """
        print(f"\n🔍 Auditor analyzing: {file_path}")
        
        # Step 1: Read the file
        code_content = read_file(file_path)
        if not code_content:
            print(f"❌ Could not read file: {file_path}")
            return {"error": "Could not read file", "issues": []}
        
        # Step 2: Get file info
        file_info = get_file_info(file_path)
        print(f"📄 File info: {file_info.get('line_count', 0)} lines")
        
        # Step 3: Run pylint analysis
        print("🔧 Running pylint analysis...")
        pylint_results = run_pylint(file_path)
        print(f"📊 Pylint score: {pylint_results.get('score', 0)}/10")
        print(f"⚠️  Pylint found {pylint_results.get('total_issues', 0)} issues")
        
        # Step 4: Prepare prompt for LLM
        user_prompt = f"""Analyse ce fichier Python et détecte TOUS les problèmes.

**FICHIER:** {Path(file_path).name}
**LIGNES:** {file_info.get('line_count', 0)}

**RÉSULTATS PYLINT:**
- Score: {pylint_results.get('score', 0)}/10
- Issues détectées: {pylint_results.get('total_issues', 0)}
- Détails: {json.dumps(pylint_results.get('issues', [])[:5], indent=2)}

**CODE SOURCE:**
```python
{code_content}
```

Retourne UNIQUEMENT du JSON valide selon le format spécifié dans le system prompt."""
        
        # Step 5: Call Gemini API
        print("🤖 Calling Gemini API for deep analysis...")
        try:
            response = self.model.generate_content(
                [
                    {"role": "user", "parts": [AUDITOR_SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Je suis prêt à analyser le code Python selon les règles définies. J'attends le code à analyser."]},
                    {"role": "user", "parts": [user_prompt]}
                ],
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 4000,
                }
            )
            
            raw_response = response.text.strip()
            print(f"✅ Received response from Gemini ({len(raw_response)} chars)")
            
            # Step 6: Parse JSON response
            # Clean markdown code blocks if present
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").replace("```", "").strip()
            elif raw_response.startswith("```"):
                raw_response = raw_response.replace("```", "").strip()
            
            analysis_result = json.loads(raw_response)
            
            # Step 7: Log the experiment
            log_experiment(
                agent_name="Auditor_Agent",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": file_path,
                    "file_lines": file_info.get('line_count', 0),
                    "pylint_score": pylint_results.get('score', 0),
                    "pylint_issues": pylint_results.get('total_issues', 0),
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "total_issues_found": analysis_result.get('summary', {}).get('total_issues', 0),
                    "critical_issues": analysis_result.get('summary', {}).get('critical_issues', 0),
                    "overall_severity": analysis_result.get('summary', {}).get('overall_severity', 'UNKNOWN')
                },
                status="SUCCESS"
            )
            
            print(f"✅ Analysis complete: {analysis_result.get('summary', {}).get('total_issues', 0)} issues found")
            return analysis_result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {raw_response[:500]}...")
            
            log_experiment(
                agent_name="Auditor_Agent",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": user_prompt,
                    "output_response": raw_response,
                    "error": f"JSON parse error: {str(e)}"
                },
                status="FAILED"
            )
            
            return {"error": "Failed to parse response", "issues": [], "raw_response": raw_response}
        
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            
            log_experiment(
                agent_name="Auditor_Agent",
                model_used=self.model_name,
                action=ActionType.ANALYSIS,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": user_prompt,
                    "output_response": "",
                    "error": str(e)
                },
                status="FAILED"
            )
            
            return {"error": str(e), "issues": []}


# Test the agent if run directly
if __name__ == "__main__":
    print("🧪 Testing Auditor Agent...")
    
    # Create a test file
    test_code = """
def divide_numbers(a, b):
    return a / b

def get_item(lst, index):
    return lst[index]

x = 10
y = 0
result = divide_numbers(x, y)
"""
    
    # Write test file
    test_file = "test_buggy_code.py"
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    # Test the agent
    auditor = AuditorAgent()
    result = auditor.analyze_file(test_file)
    
    print("\n" + "="*50)
    print("ANALYSIS RESULT:")
    print("="*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Clean up
    import os
    os.remove(test_file)