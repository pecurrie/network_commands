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


2. curl

REQUIRES OUTBOUND IP/PORT WHITELISTING to whichever port you're connecting to. 443 is open outbound everywhere so that works with no changes

```
| makeresults
| eval url_field="https://www.google.com:443"
| mycurl url_field=url_field
```

<img width="1727" height="662" alt="image" src="https://github.com/user-attachments/assets/94356dd2-8a15-4927-b817-e4e7bf10a113" />


## Installing in Splunk Cloud

The Splunk Cloud the firewall requirements are below. They can be implemented as described [here](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/9.2.2406/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/configure-ip-allow-lists-for-splunk-cloud-platform) (inbound) and [here](https://help.splunk.com/en/splunk-cloud-platform/administer/admin-config-service-manual/9.2.2406/administer-splunk-cloud-platform-using-the-admin-config-service-acs-api/configure-outbound-ports-for-splunk-cloud-platform) (outbound).

1. whois - port 43
