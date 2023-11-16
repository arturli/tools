#!/usr/bin/python3
import argparse
import requests
import base64
from datetime import datetime


def parse_mtt_data(data):
    """parse MTT Respond/Resolve data"""
    mtr_global = {}
    for item in data:
        action_started = ""
        action_in_progress = ""
        action_done = ""
        for action in item["actions"]:
            # state: todo
            if action["new_state"] == "TODO":
                action_started = datetime.strptime(
                    action["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
            # state: in_progress
            elif action["new_state"] == "IN_PROGRESS":
                action_in_progress = datetime.strptime(
                    action["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
            # state: done
            elif action["new_state"] == "DONE":
                action_done = datetime.strptime(
                    action["timestamp"], "%Y-%m-%d %H:%M:%S"
                )

        # store MTT data in key/value structure
        # key
        year_month = ".".join([str(action_started.year), str(action_started.month)])
        # value
        if year_month in mtr_global.keys():
            mtr_global[year_month]["MTTRespond"] += action_in_progress - action_started
            mtr_global[year_month]["MTTResolve"] += action_done - action_started
            mtr_global[year_month]["total_items_monthly"] += 1
        else:
            mtr_global[year_month] = {}
            mtr_global[year_month]["MTTRespond"] = action_in_progress - action_started
            mtr_global[year_month]["MTTResolve"] = action_done - action_started
            mtr_global[year_month]["total_items_monthly"] = 1
    return mtr_global


def calculate_mtt(data):
    """calculate MTT Respond/Resolve"""
    for y_t, mtt_data in data.items():
        # calculate monthly metrics
        mtt_data["MTTRespond"] = (
            mtt_data["MTTRespond"] / mtt_data["total_items_monthly"]
        )
        mtt_data["MTTResolve"] = (
            mtt_data["MTTResolve"] / mtt_data["total_items_monthly"]
        )
        # remove redundant item
        mtt_data.pop("total_items_monthly")
        mtt_data["MTTRespond"] = int(mtt_data["MTTRespond"].total_seconds() / 60)
        mtt_data["MTTResolve"] = int(mtt_data["MTTResolve"].total_seconds() / 60)

    return data


def main():
    parser = argparse.ArgumentParser(description="Monthly metrics processor.")
    parser.add_argument("webhook_url", help="Webhook URL - download and push data.")
    parser.add_argument("username", help="Username used as input header.")
    args = parser.parse_args()

    srad_header = base64.b64encode(bytes(args.username, "utf-8"))
    headers = {
        "SRAD": srad_header,
    }
    response = requests.get(args.webhook_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        mtr_global = parse_mtt_data(data)
        mtt = calculate_mtt(mtr_global)
        data = dict(sorted(mtt.items()))
        rt = requests.post(args.webhook_url, json=data, headers=headers)
        if rt.status_code == 200:
            print(data)
            print("OK: monthly metrics were sent.")
        else:
            print("ERROR: monthly metrics were not sent!")

    else:
        print("Error fetching data!")


if __name__ == "__main__":
    main()
