
# ============================================
# RUPSHA — knowledge_graph.py
# Knowledge Graph with Deduplication
# ============================================

import json
import os
from datetime import datetime
from collections import deque

import config
BASE_DIR = config.BASE_DIR
USER_NAME = config.USER_NAME


class KnowledgeGraph:
    """
    RUPSHA's long-term memory web.
    Stores facts as (subject --relation--> object) triples.
    Prevents duplicates and can find connections between ideas.
    """

    def __init__(self, filepath=None):
        if filepath is None:
            self.filepath = os.path.join(BASE_DIR, "data", "knowledge_graph.json")
        else:
            self.filepath = filepath

        self.triples = []
        self.load()


    def add_fact(self, subject, relation, obj, confidence=1.0):
        """
        Adds one fact: 'subject --relation--> object'
        """
        key = (
            str(subject).lower().strip(),
            str(relation).lower().strip(),
            str(obj).lower().strip()
        )

        for t in self.triples:
            existing = (
                str(t['subject']).lower().strip(),
                str(t['relation']).lower().strip(),
                str(t['object']).lower().strip()
            )
            if existing == key:
                if confidence > t.get('confidence', 0):
                    t['confidence'] = confidence
                return

        self.triples.append({
            'subject': subject,
            'relation': relation,
            'object': obj,
            'confidence': float(confidence),
            'timestamp': datetime.now().isoformat()
        })


    def get_facts_about(self, entity, as_subject=True, as_object=True):
        entity_clean = str(entity).lower().strip()
        results = []

        for t in self.triples:
            subj_match = as_subject and str(t['subject']).lower().strip() == entity_clean
            obj_match  = as_object  and str(t['object']).lower().strip()  == entity_clean

            if subj_match or obj_match:
                results.append(t)

        return results


    def find_path(self, start_entity, end_entity, max_depth=5):
        start = str(start_entity).lower().strip()
        end   = str(end_entity).lower().strip()

        queue = deque()
        queue.append((start, [(start, "start", start)]))
        visited = set([start])

        while queue:
            current, path = queue.popleft()

            if current == end and len(path) > 1:
                return path

            if len(path) >= max_depth:
                continue

            for t in self.triples:
                subj = str(t['subject']).lower().strip()
                obj  = str(t['object']).lower().strip()

                if subj == current and obj not in visited:
                    visited.add(obj)
                    new_path = path + [(subj, t['relation'], obj)]
                    queue.append((obj, new_path))

                if obj == current and subj not in visited:
                    visited.add(subj)
                    new_path = path + [(subj, t['relation'], obj)]
                    queue.append((subj, new_path))

        return None


    def deduplicate(self):
        seen = set()
        clean = []

        for t in self.triples:
            key = (
                str(t['subject']).lower().strip(),
                str(t['relation']).lower().strip(),
                str(t['object']).lower().strip()
            )
            if key not in seen:
                seen.add(key)
                clean.append(t)

        removed = len(self.triples) - len(clean)
        self.triples = clean
        return removed


    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.triples, f, indent=2, ensure_ascii=False)

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.triples = json.load(f)
            except json.JSONDecodeError:
                self.triples = []
        else:
            self.triples = []


    def count(self):
        return len(self.triples)

    def get_all_entities(self):
        entities = set()
        for t in self.triples:
            entities.add(t['subject'])
            entities.add(t['object'])
        return entities

    def to_text(self, max_facts=20):
        lines = []
        for t in self.triples[:max_facts]:
            lines.append(f"{t['subject']} {t['relation']} {t['object']}.")
        return "\n".join(lines)

    def clear(self):
        self.triples = []
        self.save()
