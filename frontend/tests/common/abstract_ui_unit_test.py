
class AbstractUiUnitTest():
    def get_component(self, page, object):
        for key, component in page.elements.items():
            if isinstance(component, object):
                return component
        return None