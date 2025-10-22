# network_commands
Network commands for Splunk SPL

## Usage

1. whois

REQUIRES OUTBOUND IP/PORT WHITELISTING!! (port 43)

```
| makeresults
| eval url="www.google.com"
| whois url_field=url
```
<img width="1356" height="868" alt="image" src="https://github.com/user-attachments/assets/c547623b-b58f-47be-ac60-2e1d8b68531d" />


## Installing in Splunk Cloud

The Splunk Cloud the firewall requirements are below. They can be implemented as described [here](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/9.2.2406/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/configure-ip-allow-lists-for-splunk-cloud-platform) (inbound) and [here](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/9.2.2406/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/configure-outbound-ports-for-splunk-cloud-platform) (outbound).

1. whois - port 43
