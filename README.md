# Reliable Trust Resilience

RTR is a software tool developed for the HORSE project. The purpose of the RTR is to accept a mitigation action for an attack targeting a network topology. This mitigation action is basically a JSON containing information both on the attack and the mitigation action that counters it. The RTR then extracts the useful information from this file and configures an Ansible Playbook. This Playbook is then sent to an enforcer, who uses it to configure parts of the network.

## Installation

Since this is a prototype you can download the repository and run the following command:
- uvicorn IBI-RTR_api:rtr_api
