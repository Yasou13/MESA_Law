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

