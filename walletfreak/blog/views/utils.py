import ast

def parse_tags_helper(tags):
    if not tags:
        return []
    
    parsed_tags = []
    if isinstance(tags, str):
        if tags.startswith('[') and tags.endswith(']'):
            try:
                loaded = ast.literal_eval(tags)
                if isinstance(loaded, list):
                    parsed_tags = [str(t).lower().strip() for t in loaded]
                else:
                    parsed_tags = [tags.lower().strip()]
            except:
                 parsed_tags = [t.lower().strip() for t in tags.split(',') if t.strip()]
        else:
             parsed_tags = [t.lower().strip() for t in tags.split(',') if t.strip()]
    elif isinstance(tags, list):
         # Check for single stringified list in list
         if len(tags) == 1 and isinstance(tags[0], str) and tags[0].startswith('[') and tags[0].endswith(']'):
             try:
                loaded = ast.literal_eval(tags[0])
                if isinstance(loaded, list):
                    parsed_tags = [str(t).lower().strip() for t in loaded]
                else:
                     parsed_tags = [str(t).lower().strip() for t in tags]
             except:
                 parsed_tags = [str(t).lower().strip() for t in tags]
         else:
             parsed_tags = [str(t).lower().strip() for t in tags]
    return parsed_tags
