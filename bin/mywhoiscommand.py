import sys
# Removed: import subprocess # No longer needed for system whois command
import re
from urllib.parse import urlparse
from splunklib.searchcommands import StreamingCommand, dispatch, Configuration, Option, validators

# Import the python-whois library
try:
    import whois
    # Removed: from whois.exceptions import WhoisException
    # As per user feedback, exceptions.py does not exist in their whois code.
    # We will catch a general Exception for library errors.
except ImportError as e:
    # This block handles the case where the 'whois' library itself is not found
    whois = None # Set to None if import fails
    # Log this critical failure to splunkd.log
    print(f"CRITICAL: Failed to import 'whois' library: {e}", file=sys.stderr)
    # Note: self.logger is not available at this global scope.

# Removed: WHOIS_COMMAND = "whois" # No longer needed for system whois command

# --- Actual WHOIS Lookup Function using python-whois ---
def perform_whois_lookup(url_string, logger):
    """
    Executes a WHOIS lookup for a given URL's domain using the python-whois library
    and returns parsed WHOIS data.
    """
    whois_results = {}

    if whois is None:
        logger.critical("python-whois library not found. Please ensure it's installed in the app's bin directory.")
        whois_results["whois_error"] = "python-whois library not installed or failed to import."
        whois_results["whois_lookup_success"] = "false"
        return whois_results

    domain = None
    try:
        logger.debug(f"Attempting to parse URL: {url_string}")
        parsed_url = urlparse(url_string)
        domain = parsed_url.netloc

        if not domain:
            # Handle cases like "google.com" directly without http/https
            domain = url_string.split('/')[0].split(':')[0]

        if not domain:
            logger.warning(f"Could not extract domain from URL: '{url_string}'")
            whois_results["whois_error"] = "Invalid URL or domain format"
            whois_results["whois_lookup_success"] = "false"
            return whois_results

        logger.info(f"Performing WHOIS lookup for domain: {domain} using python-whois.")

        # Perform the WHOIS lookup using the library
        # Removed 'timeout' argument as it might not be supported by older versions
        whois_entry = whois.whois(domain)

        if whois_entry:
            logger.info(f"WHOIS lookup successful for {domain}")
            whois_results["whois_lookup_success"] = "true"
            whois_results["whois_domain"] = domain # Add the looked-up domain

            # --- Extract and Process Fields from WhoisEntry ---
            # Iterate through common attributes and add them to results
            # Explicitly decode bytes to str to prevent TypeError
            for attr in [
                'registrar', 'creation_date', 'expiration_date', 'updated_date',
                'registrant_name', 'registrant_organization', 'registrant_email',
                'dnssec', 'city', 'state', 'country', 'address', 'zipcode', 'phone'
            ]:
                if hasattr(whois_entry, attr) and getattr(whois_entry, attr) is not None:
                    value = getattr(whois_entry, attr)
                    if isinstance(value, bytes):
                        try:
                            whois_results[f"whois_parsed_{attr}"] = value.decode('utf-8')
                        except UnicodeDecodeError:
                            logger.warning(f"Could not decode {attr} '{value!r}' as UTF-8. Trying latin-1.")
                            whois_results[f"whois_parsed_{attr}"] = value.decode('latin-1', errors='replace')
                    elif isinstance(value, (list, tuple)): # Handle lists (like emails)
                        whois_results[f"whois_parsed_{attr}"] = ", ".join(map(str, value))
                    else:
                        whois_results[f"whois_parsed_{attr}"] = str(value) # Ensure it's a string

            # Handle multi-value fields (e.g., name_servers, status) which are often lists
            if hasattr(whois_entry, 'name_servers') and whois_entry.name_servers:
                whois_results["whois_parsed_name_servers"] = ", ".join(map(str, whois_entry.name_servers))
            if hasattr(whois_entry, 'status') and whois_entry.status:
                if isinstance(whois_entry.status, list):
                    whois_results["whois_parsed_domain_status"] = ", ".join(map(str, whois_entry.status))
                else:
                    whois_results["whois_parsed_domain_status"] = str(whois_entry.status)

            # Add a raw output field for completeness if desired, by converting the object to string
            # Note: This won't be the exact raw WHOIS response, but a string representation of the parsed object.
            whois_results["whois_raw_object_dump"] = str(whois_entry)


        else:
            logger.warning(f"WHOIS lookup returned no data for {domain}. Domain might not exist or lookup failed silently.")
            whois_results["whois_error"] = "No WHOIS data found for domain."
            whois_results["whois_lookup_success"] = "false"

    # Catch a general Exception since WhoisException might not be available
    except Exception as e:
        logger.error(f"An error occurred during WHOIS lookup for '{url_string}': {e}", exc_info=True)
        whois_results["whois_error"] = f"WHOIS lookup error: {e}"
        whois_results["whois_lookup_success"] = "false"

    return whois_results

# --- Splunk Custom Command Class ---
@Configuration(local=True)
class MyWhoisCommand(StreamingCommand):
    """
    ##Syntax
    | mywhoiscommand url_field=<field_name>

    ##Description
    Performs WHOIS lookups for URLs found in the specified field
    of incoming events and adds parsed WHOIS details as new fields.
    """
    url_field = Option(
        require=True,
        validate=validators.Fieldname()
    )

    def stream(self, records):
        self.logger.info(f"MyWhoisCommand: Starting stream command. URL field: {self.url_field}")
        processed_count = 0

        for record in records:
            processed_count += 1
            url_to_lookup = record.get(self.url_field)

            self.logger.debug(f"MyWhoisCommand: Processing record {processed_count}. URL value: '{url_to_lookup}'")

            if url_to_lookup:
                whois_data = perform_whois_lookup(url_to_lookup, self.logger)
                record.update(whois_data)
            else:
                self.logger.warning(f"MyWhoisCommand: Field '{self.url_field}' not found or empty for record {processed_count}.")
                record["whois_error"] = "URL field not found or empty in input event"
                record["whois_lookup_success"] = "false"

            yield record

        self.logger.info(f"MyWhoisCommand: Finished streaming {processed_count} records.")

if __name__ == '__main__':
    dispatch(MyWhoisCommand, sys.argv)
