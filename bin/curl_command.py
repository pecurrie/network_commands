import sys
import requests # Import the requests library
from splunklib.searchcommands import StreamingCommand, dispatch, Configuration, Option, validators

# --- Actual HTTP Request Function using requests library ---
def perform_http_request(url_string, logger):
    """
    Executes an HTTP GET request for a given URL using the requests library
    and returns relevant response data. This mimics 'curl -v' by capturing
    headers, status, and body.
    """
    request_results = {}
    if not url_string:
        logger.warning("No URL string provided for HTTP request.")
        request_results["http_error"] = "No URL provided"
        request_results["http_lookup_success"] = "false"
        return request_results

    try:
        logger.info(f"Performing HTTP GET request for URL: {url_string} using requests library.")

        # Perform the GET request with a timeout (mimics curl --max-time)
        # allow_redirects=True by default, mimics curl's default behavior
        response = requests.get(url_string, timeout=30, verify=False) # verify=False for self-signed certs, consider removing in production

        request_results["http_lookup_success"] = "true"
        request_results["http_url"] = response.url # Final URL after redirects
        request_results["http_status_code"] = str(response.status_code)
        request_results["http_reason"] = response.reason # e.g., "OK", "Not Found"
        request_results["http_elapsed_time_seconds"] = str(response.elapsed.total_seconds())

        # Request Headers
        request_results["http_request_headers"] = str(response.request.headers)

        # Response Headers (mimics part of curl -v output)
        response_headers_str = ""
        for header, value in response.headers.items():
            response_headers_str += f"{header}: {value}\n"
        request_results["http_response_headers"] = response_headers_str.strip()

        # Body Content (mimics curl's default output)
        request_results["http_body_content"] = response.text

        # Check for HTTP errors (e.g., 4xx, 5xx status codes)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        logger.info(f"HTTP request successful for {url_string} (Status: {response.status_code})")

    except requests.exceptions.Timeout as e:
        logger.error(f"HTTP request timed out for '{url_string}': {e}")
        request_results["http_error"] = f"Request timed out: {e}"
        request_results["http_lookup_success"] = "false"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"HTTP connection error for '{url_string}': {e}")
        request_results["http_error"] = f"Connection error: {e}"
        request_results["http_lookup_success"] = "false"
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for '{url_string}': {e} (Status: {e.response.status_code})")
        request_results["http_error"] = f"HTTP error: {e.response.status_code} {e.response.reason}"
        request_results["http_lookup_success"] = "false"
        # Still include status code and headers for HTTP errors if available
        request_results["http_status_code"] = str(e.response.status_code)
        request_results["http_reason"] = e.response.reason
        request_results["http_response_headers"] = str(e.response.headers)
        request_results["http_body_content"] = e.response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"An unexpected requests error occurred for '{url_string}': {e}", exc_info=True)
        request_results["http_error"] = f"Unexpected requests error: {e}"
        request_results["http_lookup_success"] = "false"
    except Exception as e:
        logger.error(f"An general error occurred during HTTP request for '{url_string}': {e}", exc_info=True)
        request_results["http_error"] = f"General error: {e}"
        request_results["http_lookup_success"] = "false"

    return request_results

# --- Splunk Custom Command Class ---
@Configuration(local=True)
class MyCurlCommand(StreamingCommand): # Keep the class name consistent with commands.conf
    """
    ##Syntax
    | mycurl url_field=<field_name>

    ##Description
    Performs an HTTP GET request using the Python 'requests' library on the value
    of the specified field and adds the response details as new fields to the event.
    """
    url_field = Option(
        require=True,
        validate=validators.Fieldname()
    )

    def stream(self, records):
        self.logger.info(f"MyCurlCommand: Starting stream command. URL field: {self.url_field}")
        processed_count = 0

        for record in records:
            processed_count += 1
            url_to_request = record.get(self.url_field)

            self.logger.debug(f"MyCurlCommand: Processing record {processed_count}. URL value: '{url_to_request}'")

            if url_to_request:
                http_data = perform_http_request(url_to_request, self.logger)
                record.update(http_data)
            else:
                self.logger.warning(f"MyCurlCommand: Field '{self.url_field}' not found or empty for record {processed_count}.")
                record["http_error"] = "URL field not found or empty in input event"
                record["http_lookup_success"] = "false"

            yield record

        self.logger.info(f"MyCurlCommand: Finished streaming {processed_count} records.")

if __name__ == '__main__':
    dispatch(MyCurlCommand, sys.argv)
