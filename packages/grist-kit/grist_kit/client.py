"""Client REST de l'API Grist."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

HOTE_PAR_DEFAUT = "https://grist.numerique.gouv.fr/api"


class GristErreur(RuntimeError):
    """Erreur de l'API Grist, au message lisible (pas de trace brute)."""


def _message(code: int, corps: str) -> str:
    detail = (corps or "").strip()[:300]
    if code == 403:
        return (
            "403 : accès refusé. Soit le pare-feu a refusé le corps de la requête "
            "(motifs de piratage détectés, même dans une donnée), soit la clé d'API "
            f"n'a pas les droits sur ce document. Détail : {detail}"
        )
    if code == 413:
        return (
            "413 : requête trop volumineuse pour l'API (limite autour de 1 Mo). "
            f"Réduire le contenu envoyé (ex. bundle de widget). Détail : {detail}"
        )
    return f"HTTP {code}. Détail : {detail}"


class GristClient:
    """Client pour interagir avec l'API Grist."""

    # Cadence : au-delà de quelques dizaines de requêtes d'affilée, le pare-feu bloque tout
    # (lectures comprises) pendant plusieurs minutes. 0 pour la désactiver.
    cadence = 0.6
    pause_refus = 3

    def __init__(self, api_key: Optional[str] = None, doc_id: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("GRIST_API_KEY")
        self.doc_id = doc_id or os.getenv("GRIST_DOC_ID")
        self.base_url = base_url or os.getenv("GRIST_API_HOST", HOTE_PAR_DEFAUT)

        if not self.api_key:
            raise ValueError("GRIST_API_KEY non définie")
        if not self.doc_id:
            raise ValueError("GRIST_DOC_ID non défini")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._session = requests.Session()
        self._derniere = 0.0
        logger.info("GristClient initialisé - Document: %s", self.doc_id)

    def _make_request(self, method: str, endpoint: str, data: Optional[Any] = None) -> Any:
        """Requête vers /docs/<doc>/<endpoint> ; renvoie le JSON, lève GristErreur si HTTP non 2xx."""
        if method not in ("GET", "POST", "PATCH", "DELETE"):
            raise ValueError(f"Méthode HTTP non supportée: {method}")
        url = f"{self.base_url}/docs/{self.doc_id}{endpoint}"

        attente = self.cadence - (time.monotonic() - self._derniere)
        if attente > 0:
            time.sleep(attente)

        # Le serveur répond parfois par un 302 « Loading » vers la même adresse (document affecté à un
        # worker, cookie à poser). `requests` rejouerait alors un POST en GET : l'écriture serait prise
        # pour une lecture et ignorée sans erreur. On rejoue donc la MÊME méthode, avec les cookies reçus.
        refus = 0
        for _ in range(8):
            response = self._session.request(
                method, url, headers=self.headers, json=data, timeout=30, allow_redirects=False
            )
            if response.status_code in (301, 302, 303, 307, 308) and response.headers.get("Location"):
                url = response.headers["Location"]
                continue
            # Le pare-feu (Incapsula) refuse parfois une requête saine, puis l'accepte telle quelle.
            if response.status_code == 403 and "Incapsula" in response.text and refus < 2:
                refus += 1
                time.sleep(self.pause_refus)
                continue
            break
        self._derniere = time.monotonic()

        if response.status_code >= 400:
            msg = _message(response.status_code, response.text)
            logger.error("Erreur requête Grist %s %s: %s", method, endpoint, msg)
            raise GristErreur(msg)
        return response.json()

    def fetch_table(self, table_name: str) -> List[Dict]:
        """Tous les enregistrements d'une table."""
        return self._make_request("GET", f"/tables/{table_name}/records").get("records", [])

    def add_record(self, table_name: str, data: Dict) -> int:
        """Ajoute un enregistrement ; renvoie son id."""
        payload = {"records": [{"fields": data}]}
        result = self._make_request("POST", f"/tables/{table_name}/records", payload)
        return result.get("records", [{}])[0].get("id")

    def update_record(self, table_name: str, record_id: int, updates: Dict) -> None:
        """Met à jour les champs d'un enregistrement."""
        payload = {"records": [{"id": record_id, "fields": updates}]}
        self._make_request("PATCH", f"/tables/{table_name}/records", payload)
