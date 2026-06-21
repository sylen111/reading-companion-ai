memory_store = {
    "category": {},
    "item": {}
}


def get_memory(annotation_type: str, text: str):

    return {
        "category_fail_count":
            memory_store["category"].get(
                annotation_type,
                0
            ),

        "item_fail_count":
            memory_store["item"].get(
                text.lower(),
                0
            )
    }


def increase_fail_count(annotation_type: str, text: str):

    memory_store["category"][annotation_type] = (
        memory_store["category"].get(
            annotation_type,
            0
        ) + 1
    )

    key = text.lower()

    memory_store["item"][key] = (
        memory_store["item"].get(
            key,
            0
        ) + 1
    )