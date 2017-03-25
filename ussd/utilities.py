import importlib
import inspect
import json

def str_to_class(import_path):
    module_name, class_name = import_path.rsplit(".", 1)
    try:
        module_ = importlib.import_module(module_name)
        try:
            class_ = getattr(module_, class_name)
        except AttributeError:
            raise Exception('Class does not exist')
    except ImportError:
        raise Exception('Module does not exist')
    return class_


def get_variables_from_response_obj(response):
    response_varialbes = {}

    for i in inspect.getmembers(response):
        # Ignores anything starting with underscore
        # (that is, private and protected attributes)
        if not i[0].startswith('_'):
            # Ignores methods
            if not inspect.ismethod(i[1]) and \
                            type(i[1]) in \
                            (str, dict, int, dict, float, list, tuple):
                if len(i) == 2:
                    response_varialbes.update(
                        {i[0]: i[1]}
                    )

    try:
        response_content = json.loads(response.content.decode())
    except json.JSONDecodeError:
        response_content = response.content.decode()

    if isinstance(response_content, dict):
        response_varialbes.update(
            response_content
        )

    # update content to save the one that has been decoded
    response_varialbes.update(
        {"content": response_content}
    )

    return response_varialbes