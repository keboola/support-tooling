import streamlit as st
import requests

# Replace these with your API details


def get_vendors(url, headers, offset=0, limit=1000):
    """Fetch objects with pagination."""
    params = {"offset": f'{offset}', "limit": f'{limit}'}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()


def delete_vendor(url, headers, vendor_id):
    """Send a DELETE request for a specific object."""
    url = f"{url}/{vendor_id}"
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response

st.title("Remove Vendors")

auth_token = st.text_input("Keboola Dev Portal Session Token", type="password")
base_url = "https://apps-api.keboola.com/admin/vendors"
headers = {'Authorization': f'{auth_token}'}

email_to_delete = st.text_input("Email of vendor to delete")


offset = 0
limit = 1000
vendors = []
all_vendprs_to_delete = [];

# Fetch objects from the API
st.write("GETTING VENDORS:")
data = get_vendors(base_url, headers, offset=offset, limit=limit)
st.write("retrieved " + str(len(data)) + " vendors")
# Exit if no more objects to process

# Filter objects with the specific email
vendors_to_delete = [obj for obj in data if obj.get("email") == email_to_delete]
vendors.extend(data)
all_vendprs_to_delete.extend(vendors_to_delete)
offset += limit


st.write("<-- all vendors -->")
st.write(str(len(vendors)))
st.write("<-- all vendors to delete -->")
st.write(str(len(all_vendprs_to_delete)))
for vendor in all_vendprs_to_delete:
    st.write(vendor)

delete_vendors = st.button("Delete these vendors?")

if delete_vendors:
    for vendor_to_delete in all_vendprs_to_delete:
        if vendor_to_delete['isApproved'] == False:
            delete_vendor(base_url, headers, vendor_to_delete['id'])
            st.success("deleted vendor " + vendor_to_delete['id'])
