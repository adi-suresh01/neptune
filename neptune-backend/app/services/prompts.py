from typing import List, Dict


def topic_extraction_prompt(notes: List[Dict[str, str]]) -> str:
    joined = "\n\n".join(
        f"NoteID: {note['id']}\nContent: {note['content'][:2000]}" for note in notes
    )
    return (
        "For each note below, generate a single general topic word that best summarizes it.\n"
        "Return JSON as a list of objects: [{\"id\": \"<note_id>\", \"topic\": \"<topic>\"}].\n"
        "Use lowercase topics and one word per topic.\n\n"
        f"{joined}"
    )


def relationship_prompt(pairs: List[Dict[str, str]]) -> str:
    joined = "\n".join(
        f"{pair['a']} | {pair['b']}" for pair in pairs
    )
    return (
        "Score relationship strength for each topic pair on a 0.0 to 1.0 scale.\n"
        "Return JSON as a list: [{\"a\": \"topic1\", \"b\": \"topic2\", \"score\": 0.0}].\n"
        "Pairs:\n"
        f"{joined}"
    )
