import datetime

import streamlit as st
from streamlit.components.v1 import html

LIVE_TAIL_URL = "https://app.datadoghq.eu/logs/livetail?query=%40component%3A{component_id}%20%40priority%3A%28ERROR%20OR%20CRITICAL%20OR%20EMERGENCY%29%20&agg_m=count&agg_m_source=base&agg_t=count&cols=host%2Cservice&fromUser=true&messageDisplay=inline&refresh_mode=sliding&storage=live&stream_sort=desc&view=spans&viz=stream&live=true"

POD_STATS = "https://app.datadoghq.eu/dashboard/9ku-8g9-5b2/job-queue-daemon?fromUser=true&refresh_mode=paused&tpl_var_componentid[0]={component_id}&tpl_var_container_name[0]={job_id}-{job_id}--0-{component_id_norm}&tpl_var_pod_name[0]=job-{job_id}&from_ts={timestamp_from}&to_ts={timestamp_to}&live=false"

CONTAINER_STATS = "https://app.datadoghq.eu/containers?query=short_image:{component_id} AND container_name:{job_id}-{job_id}--0-{component_id_norm}&selectedTopGraph=timeseries"

FROM_TO_TIMESTAMP = "from_ts={timestamp_from}&to_ts={timestamp_to}"


def open_page(url):
    open_script = """
        <script type="text/javascript">
            window.open('%s', '_blank').focus();
        </script>
    """ % (url)
    html(open_script)


def display_content():
    # stack = st.multiselect("Stack", ["eu-central-1.keboola.com",
    #                                  "keboola.com",
    #                                  "north-europe.azure.keboola.com",
    #                                  "europe-west2.gcp.keboola.com",
    #                                  "europe-west3.gcp.keboola.com",
    #                                  "us-east4.gcp.keboola.com"], key='ddstack')

    # only_keboola = st.checkbox("Show Only Keboola components", key='ddkeboola')
    # components = kbc.kbcapi_scripts.list_all_components(only_keboola)
    # component_id = st.selectbox('Enter the Component ID', [cid for cid in components], help="e.g. kds-team.ex-hubspot",
    #                             key='ddcomp')

    st.subheader("Component monitoring")
    stack = st.selectbox("Stack", ["eu-central-1.keboola.com",
                                   "keboola.com",
                                   "north-europe.azure.keboola.com",
                                   "europe-west2.gcp.keboola.com",
                                   "europe-west3.gcp.keboola.com",
                                   "us-east4.gcp.keboola.com"], key='ddstack')

    component_id = st.text_input('Enter the Component ID', help="e.g. kds-team.ex-hubspot", key='ddcomp')
    run_id = st.text_input('Job ID', help="e.g. 123123", key='ddrun')
    url = LIVE_TAIL_URL.format(component_id=component_id)
    if run_id:
        url += f"%20%40runId%3A{run_id}"

    st.link_button("Live Tail Error Stream", type="primary",
                   url=LIVE_TAIL_URL.format(component_id=component_id))

    # ### POD STATS

    # datetime from and to elements with date picker
    col1, col2 = st.columns(2)
    with col1:
        dfrom_date = st.date_input('From Date', key='ddfrom_date')
        dto_date = st.date_input('To Date', key='ddto_date')

    with col2:
        dfrom_time = st.time_input('From Time', key='ddfrom_time')
        dto_time = st.time_input('To Time', key='ddto_time')

    # Combine date and time into datetime objects
    dfrom_datetime = datetime.datetime.combine(dfrom_date, dfrom_time)
    dto_datetime = datetime.datetime.combine(dto_date, dto_time)
    # validate
    pod_help = ''
    disabled = False
    if not component_id or not run_id or not stack:
        pod_help = "Stack, Component ID and Job ID are required."
        disabled = True

    st.link_button("Job Memory Analysis / Pod Stats",
                   url=POD_STATS.format(component_id=component_id,
                                        component_id_norm=component_id.replace('.', '-'), stack=stack,
                                        job_id=run_id, timestamp_from=int(dfrom_datetime.timestamp() * 1000),
                                        timestamp_to=int(dto_datetime.timestamp() * 1000)),
                   disabled=disabled, help=pod_help, type="primary")

    # CONTAINER STATS
    con_url = CONTAINER_STATS.format(component_id=component_id,
                                     component_id_norm=component_id.replace('.', '-'), stack=stack,
                                     job_id=run_id)
    if dfrom_datetime and dto_datetime:
        con_url += FROM_TO_TIMESTAMP.format(timestamp_from=int(dfrom_datetime.timestamp() * 1000),
                                            timestamp_to=int(dto_datetime.timestamp() * 1000))
    if not component_id or not run_id:
        pod_help = "Component ID and Job ID are required."
        disabled = True
    st.link_button("Container Analysis / Processes",
                   url=con_url, disabled=disabled, help=pod_help, type="primary")

    st.divider()

    st.subheader("App Errors Monitoring")

    exception_id = st.text_input('Exception ID', help="e.g. exception-123456", key='ddex')
    st.link_button("Show Errors", type="primary",
                   url=LIVE_TAIL_URL.format(component_id=component_id))

    st.divider()
    st.empty()
