"""
==============================================================================
BiosenseLink - Conector con la API Local de Ollama
==============================================================================
Modulo de comunicacion de bajo nivel con el servidor de inferencia Ollama.
Utiliza exclusivamente librerias nativas de Python (urllib, json) para
eliminar dependencias externas y garantizar la portabilidad del sistema.

El conector implementa:
  - Comunicacion HTTP con la API REST de Ollama (puerto 11434).
  - Modo de salida JSON forzado ("format": "json") para interoperabilidad.
  - Gestion de timeouts configurables para modelos pesados.
  - Verificacion de disponibilidad del servidor antes de la inferencia.

Referencia tecnica:
  API de Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


# ---------------------------------------------------------------------------
# Configuracion del servidor
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "biosenselink-cdss"
REQUEST_TIMEOUT = 300  # Segundos. DeepSeek-R1 necesita ~60s para procesar el prompt clinico + ~120s para CoT


def check_server_health() -> bool:
    """
    Verifica que el servidor de Ollama este activo y respondiendo.

    Returns:
        True si el servidor responde correctamente, False en caso contrario.
    """
    try:
        req = urllib.request.Request(OLLAMA_BASE_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError):
        return False


def list_available_models() -> list:
    """
    Obtiene la lista de modelos disponibles en el servidor Ollama local.

    Returns:
        Lista de diccionarios con la informacion de cada modelo.
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("models", [])
    except Exception as e:
        print(f"[ERROR] No se pudo obtener la lista de modelos: {e}")
        return []


def check_model_available(model_name: str = OLLAMA_MODEL) -> bool:
    """
    Verifica que el modelo especificado este disponible en Ollama.

    Args:
        model_name: Nombre del modelo a verificar.

    Returns:
        True si el modelo existe, False en caso contrario.
    """
    models = list_available_models()
    available_names = [m.get("name", "").split(":")[0] for m in models]
    return model_name.split(":")[0] in available_names


def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = OLLAMA_MODEL,
    json_mode: bool = True,
    temperature: float = 0.0,
    timeout: int = REQUEST_TIMEOUT,
) -> Dict[str, Any]:
    """
    Envia un prompt al modelo de Ollama y obtiene la respuesta completa.

    Utiliza el endpoint /api/generate con stream=true (modo streaming)
    para mantener el socket activo durante la carga del modelo en RAM
    y la generacion de la cadena de razonamiento Chain-of-Thought.

    En modo streaming, Ollama envia fragmentos NDJSON progresivamente.
    Cada linea contiene un JSON con el campo "response" parcial.
    La ultima linea tiene "done": true y contiene las metricas finales.

    Args:
        prompt: Texto del prompt del usuario.
        system_prompt: Prompt de sistema opcional (sobreescribe el del Modelfile).
        model: Nombre del modelo de Ollama a utilizar.
        json_mode: Si True, fuerza la salida en formato JSON valido.
        temperature: Temperatura de muestreo (0.0 = determinista).
        timeout: Timeout del socket por fragmento en segundos.

    Returns:
        Diccionario con la respuesta completa de Ollama.

    Raises:
        ConnectionError: Si el servidor de Ollama no esta disponible.
        TimeoutError: Si no se recibe ningun fragmento en {timeout} segundos.
    """
    # Verificar disponibilidad del servidor
    if not check_server_health():
        raise ConnectionError(
            "El servidor de Ollama no esta disponible en "
            f"{OLLAMA_BASE_URL}. Asegurate de que Ollama esta ejecutandose."
        )

    # Construir el payload con streaming activado
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
        }
    }

    if system_prompt:
        payload["system"] = system_prompt

    if json_mode:
        payload["format"] = "json"

    # Serializar y enviar
    url = f"{OLLAMA_BASE_URL}/api/generate"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        response = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        raise ConnectionError(f"Error de conexion con Ollama: {e}")

    # Leer fragmentos NDJSON de forma progresiva
    accumulated_response = ""
    final_result = {}
    token_count = 0

    try:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Acumular la respuesta parcial
            partial = chunk.get("response", "")
            accumulated_response += partial
            token_count += 1

            # Indicador de progreso en consola (cada 50 tokens)
            if token_count % 50 == 0:
                import sys
                sys.stdout.write(".")
                sys.stdout.flush()

            # La ultima linea contiene done=true y las metricas
            if chunk.get("done", False):
                final_result = chunk
                break

    except TimeoutError:
        raise TimeoutError(
            f"No se recibieron datos del modelo en {timeout}s. "
            "Verifica que el modelo esta cargado correctamente."
        )
    finally:
        response.close()

    # Construir resultado unificado (compatible con formato no-streaming)
    final_result["response"] = accumulated_response

    # Calcular metricas de rendimiento
    eval_count = final_result.get("eval_count", 0)
    eval_duration_ns = final_result.get("eval_duration", 1)
    tokens_per_second = (eval_count / eval_duration_ns) * 1e9 if eval_duration_ns > 0 else 0
    total_duration_s = final_result.get("total_duration", 0) / 1e9

    final_result["_performance"] = {
        "tokens_generated": eval_count,
        "generation_speed_tps": round(tokens_per_second, 1),
        "total_time_seconds": round(total_duration_s, 2),
    }

    if token_count > 50:
        print()  # Nueva linea tras los puntos de progreso

    return final_result


def parse_json_response(ollama_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae y valida el JSON de la respuesta del modelo.

    DeepSeek-R1 a menudo incluye bloques de razonamiento <think>...</think>
    antes del JSON final. Esta funcion extrae exclusivamente el JSON valido.

    Args:
        ollama_result: Respuesta cruda de la funcion generate().

    Returns:
        Diccionario Python parseado del JSON del modelo.

    Raises:
        ValueError: Si no se encuentra JSON valido en la respuesta.
    """
    response_text = ollama_result.get("response", "")

    # Intentar parsear directamente
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # DeepSeek-R1 puede envolver el JSON en bloques <think>
    # Buscar el primer '{' y el ultimo '}'
    start = response_text.find("{")
    end = response_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        json_candidate = response_text[start:end + 1]
        try:
            return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "No se encontro JSON valido en la respuesta del modelo. "
        f"Respuesta recibida (primeros 500 chars): {response_text[:500]}"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("  BiosenseLink - Diagnostico del Conector Ollama")
    print("=" * 60)

    # Test 1: Servidor
    server_ok = check_server_health()
    print(f"\n  [1] Servidor Ollama:  {'OK' if server_ok else 'NO DISPONIBLE'}")

    if server_ok:
        # Test 2: Modelos disponibles
        models = list_available_models()
        print(f"  [2] Modelos locales:  {len(models)} encontrados")
        for m in models:
            print(f"       - {m.get('name', 'N/A')} ({m.get('size', 0) / 1e9:.1f} GB)")

        # Test 3: Modelo CDSS
        cdss_ok = check_model_available(OLLAMA_MODEL)
        print(f"  [3] Agente CDSS:     {'COMPILADO' if cdss_ok else 'NO ENCONTRADO'}")

        if cdss_ok:
            # Test 4: Inferencia rapida
            print(f"\n  [4] Test de inferencia con {OLLAMA_MODEL}...")
            result = generate(
                prompt="Responde SOLO con un JSON: {\"status\": \"ok\", \"model\": \"biosenselink-cdss\"}",
                json_mode=True,
                timeout=180,
            )
            perf = result.get("_performance", {})
            print(f"       Tokens generados: {perf.get('tokens_generated', 'N/A')}")
            print(f"       Velocidad:        {perf.get('generation_speed_tps', 'N/A')} tokens/s")
            print(f"       Tiempo total:     {perf.get('total_time_seconds', 'N/A')}s")
            parsed = parse_json_response(result)
            print(f"       JSON valido:      {json.dumps(parsed, indent=2)}")

    print("\n" + "=" * 60)
