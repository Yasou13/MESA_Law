"""Legal Extraction — extracts structured entities (claims, dates, parties) from parsed text using heuristics and regex."""
import logging
import re

from apps.api.core.extraction import LegalExtractionAdapter

logger = logging.getLogger("api.services.legal_extraction")

class HeuristicLegalExtractionAdapter(LegalExtractionAdapter):
    async def extract_claims(self, text: str) -> list[dict]:
        logger.info("HeuristicLegalExtractionAdapter: Extracting claims from text")
        if not text or not text.strip():
            return []
            
        lines_or_sentences = re.split(r'[\n.!?]+', text)
        keywords = [
            "claim", "breach", "damage", "liable", "violat", "negligen", "indemni", "demand", "fai", "owe", "duty", "alleg", "disput", "unlawful",
            "tazminat", "ihbar", "kıdem", "alacak", "borçlu", "fazla mesai", "haksız fesih", "ihtar", "sözleşmeye aykırı", "dava", "zarar", "talep", "ihlal", "kusur"
        ]
        
        extracted_claims = []
        for sentence in lines_or_sentences:
            cleaned = sentence.strip()
            if len(cleaned) < 15 or len(cleaned) > 500:
                continue
            lower_s = cleaned.lower()
            for kw in keywords:
                if kw in lower_s:
                    extracted_claims.append({
                        "description": cleaned,
                        "confidence": 0.88,
                        "source_locator": f"Keyword match ('{kw}')",
                        "version": "heuristic-tr-v2.0"
                    })
                    break
            if len(extracted_claims) >= 10:
                break
                
        return extracted_claims
        
    async def extract_parties(self, text: str) -> list[dict]:
        logger.info("HeuristicLegalExtractionAdapter: Extracting parties from text")
        if not text or not text.strip():
            return []
            
        parties = []
        seen_names = set()
        
        def add_party(name: str, role: str, confidence: float = 0.90, locator: str = "Regex pattern match"):
            clean_name = name.strip(' .,\t\n\r"\'[]()')
            if len(clean_name) < 2 or len(clean_name) > 100 or clean_name.lower() in seen_names:
                return
            seen_names.add(clean_name.lower())
            
            org_keywords = [
                "corp", "inc", "llc", "ltd", "company", "co.", "association", "bank", "group", "partners", "solutions", "technologies", "global", "holdings",
                "a.ş.", "ltd.", "şti.", "san.", "tic.", "bankası", "derneği", "vakfı", "belediyesi", "müdürlüğü", "şirketi", "hastanesi", "üniversitesi"
            ]
            party_type = "ORGANIZATION" if any(kw in clean_name.lower() for kw in org_keywords) else "PERSON"
            parties.append({
                "name": clean_name,
                "role": role,
                "type": party_type,
                "confidence": confidence,
                "source_locator": locator,
                "version": "heuristic-tr-v2.0"
            })
            
        # Pattern 1: Plaintiff v. Defendant (English / Universal)
        v_match = re.search(r"([A-ZÇĞİÖŞÜ][A-Za-zçğıöşü0-9\s,._&'-]{2,50})\s+(?:v\.|vs\.|versus|-)\s+([A-ZÇĞİÖŞÜ][A-Za-zçğıöşü0-9\s,._&'-]{2,50})", text)
        if v_match:
            add_party(v_match.group(1), "PLAINTIFF", 0.92, "Case title pattern match")
            add_party(v_match.group(2), "DEFENDANT", 0.92, "Case title pattern match")
            
        # Pattern 2: Explicit Plaintiff / Defendant / Turkish labels
        p_match = re.search(r"(?i)(?:plaintiff|claimant|applicant|davacı|alacaklı|işçi|müşteki|başvuran)[:\s]+([A-ZÇĞİÖŞÜa-zçğıöşü0-9\s,._&'-]{2,50})", text)
        if p_match:
            add_party(p_match.group(1), "PLAINTIFF", 0.90, "Explicit role label match")
            
        d_match = re.search(r"(?i)(?:defendant|respondent|davalı|borçlu|işveren|şüpheli|sanık)[:\s]+([A-ZÇĞİÖŞÜa-zçğıöşü0-9\s,._&'-]{2,50})", text)
        if d_match:
            add_party(d_match.group(1), "DEFENDANT", 0.90, "Explicit role label match")
            
        # If still missing roles, check for capitalized entities in header without inventing names
        if not parties:
            header_text = text[:500]
            words = re.findall(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)+\b", header_text)
            for i, w in enumerate(words[:2]):
                role = "PLAINTIFF" if i == 0 else "DEFENDANT"
                add_party(w, role, 0.65, "Header capitalized entity inference")
                
        return parties

    async def extract_events(self, text: str) -> list[dict]:
        logger.info("HeuristicLegalExtractionAdapter: Extracting events from text")
        if not text or not text.strip():
            return []
            
        events = []
        
        # Trigger detection patterns for Turkish legal events
        trigger_patterns = [
            {
                "pattern": r'\btebliğ\b',
                "trigger_event": "Tebliğ / Notification",
                "rules": [
                    {"rule_name": "İstinaf - 14 Gün", "offset_days": 14, "reference": "HMK 345"},
                    {"rule_name": "Temyiz - 30 Gün", "offset_days": 30, "reference": "HMK 361"},
                ]
            },
            {
                "pattern": r'\bicra\s+emri\b',
                "trigger_event": "İcra Emri Tebliği",
                "rules": [
                    {"rule_name": "İcranın Geri Bırakılması - 7 Gün", "offset_days": 7, "reference": "İİK 33"},
                ]
            },
            {
                "pattern": r'\bödeme\s+emri\b',
                "trigger_event": "Ödeme Emri Tebliği",
                "rules": [
                    {"rule_name": "İtiraz Süresi - 7 Gün", "offset_days": 7, "reference": "İİK 62"},
                ]
            },
            {
                "pattern": r'\bihtarname\b',
                "trigger_event": "İhtarname Tebliği",
                "rules": [
                    {"rule_name": "Yanıt Süresi - 30 Gün", "offset_days": 30, "reference": "TBK 117"},
                ]
            },
        ]
        
        for tp in trigger_patterns:
            if re.search(tp["pattern"], text, re.IGNORECASE):
                for rule in tp["rules"]:
                    events.append({
                        "trigger_event": tp["trigger_event"],
                        "rule_name": rule["rule_name"],
                        "offset_days": rule["offset_days"],
                        "description": f"{tp['trigger_event']} tespit edildi. {rule['rule_name']} süresi başlayabilir. ({rule['reference']})",
                        "confidence": 0.85,
                        "provenance": tp["trigger_event"].lower(),
                        "legal_reference": rule["reference"],
                        "version": "heuristic-tr-v2.1"
                    })
                    
        # Date extraction from text
        date_pattern = r'(\d{1,2})[./](\d{1,2})[./](\d{4})'
        date_matches = re.findall(date_pattern, text)
        for match in date_matches:
            for event in events:
                if "date" not in event:
                    event["detected_date"] = f"{match[2]}-{match[1].zfill(2)}-{match[0].zfill(2)}"
                    break
                    
        return events
        
    async def extract_evidence(self, text: str) -> list[dict]:
        logger.info("HeuristicLegalExtractionAdapter: Extracting evidence from text")
        if not text or not text.strip():
            return []
            
        evidence = []
        keywords = ["ek-1", "ek 1", "exhibit a", "delil", "fatura", "dekont", "sözleşme örneği", "tutanak"]
        lines = text.split('\n')
        for line in lines:
            if len(line.strip()) > 100:
                continue
            lower_line = line.lower()
            for kw in keywords:
                if kw in lower_line:
                    evidence.append({
                        "description": line.strip(),
                        "relevance": "High",
                        "confidence": 0.80,
                        "provenance": kw
                    })
                    break
        return evidence


class LLMEnhancedExtractionAdapter(LegalExtractionAdapter):
    """
    Tier 2 extraction adapter that uses heuristic extraction as baseline
    and optionally enhances results with LLM-based extraction.
    
    Falls back gracefully to heuristic-only when LLM is unavailable.
    """
    
    def __init__(self):
        self._heuristic = HeuristicLegalExtractionAdapter()
        self._llm_available: bool | None = None
    
    async def _check_llm(self):
        """Check if LLM client is available and not mock."""
        if self._llm_available is None:
            try:
                from apps.api.core.llm_client import get_llm_client, LLMProvider
                client = get_llm_client()
                self._llm_available = client.config.provider != LLMProvider.MOCK
            except Exception:
                self._llm_available = False
        return self._llm_available
    
    async def _llm_extract(self, text: str, task: str) -> list[dict]:
        """Use LLM for extraction if available."""
        if not await self._check_llm():
            return []
            
        try:
            import json
            from apps.api.core.llm_client import get_llm_client, LLMMessage, LEGAL_EXTRACTION_SYSTEM_PROMPT
            
            client = get_llm_client()
            messages = [
                LLMMessage(role="system", content=LEGAL_EXTRACTION_SYSTEM_PROMPT),
                LLMMessage(role="user", content=f"Görev: {task}\n\nMetin:\n{text[:3000]}")
            ]
            
            response = await client.complete(messages)
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning(f"LLM returned non-JSON for {task}, using heuristic only")
                return []
        except Exception as e:
            logger.warning(f"LLM extraction failed for {task}: {e}")
            return []
    
    async def extract_claims(self, text: str) -> list[dict]:
        heuristic_results = await self._heuristic.extract_claims(text)
        llm_results = await self._llm_extract(text, "Talepleri ve iddiaları çıkar")
        return self._merge_results(heuristic_results, llm_results, key="description")
    
    async def extract_parties(self, text: str) -> list[dict]:
        heuristic_results = await self._heuristic.extract_parties(text)
        llm_results = await self._llm_extract(text, "Tarafları (davacı, davalı, müdahil) çıkar")
        return self._merge_results(heuristic_results, llm_results, key="name")
    
    async def extract_events(self, text: str) -> list[dict]:
        heuristic_results = await self._heuristic.extract_events(text)
        llm_results = await self._llm_extract(text, "Hukuki olayları ve süre tetikleyicilerini çıkar")
        return self._merge_results(heuristic_results, llm_results, key="trigger_event")
    
    async def extract_evidence(self, text: str) -> list[dict]:
        heuristic_results = await self._heuristic.extract_evidence(text)
        llm_results = await self._llm_extract(text, "Delilleri ve ekleri çıkar")
        return self._merge_results(heuristic_results, llm_results, key="description")
    
    @staticmethod
    def _merge_results(heuristic: list[dict], llm: list[dict], key: str) -> list[dict]:
        """Merge heuristic and LLM results, preferring heuristic for duplicates."""
        if not llm:
            return heuristic
        
        seen_keys = set()
        for item in heuristic:
            k = item.get(key, "").lower().strip()
            if k:
                seen_keys.add(k)
        
        merged = list(heuristic)
        for item in llm:
            k = item.get(key, "").lower().strip()
            if k and k not in seen_keys:
                item["source"] = "llm"
                merged.append(item)
                seen_keys.add(k)
        
        return merged

