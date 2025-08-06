import sys
from splunklib.searchcommands import GeneratingCommand, dispatch, Configuration

@Configuration(local=True)
class TestCommand(GeneratingCommand):
    def generate(self):
        yield {'_time': 1234567890, 'message': 'Hello from test command!'}

if __name__ == '__main__':
    dispatch(TestCommand, sys.argv)
