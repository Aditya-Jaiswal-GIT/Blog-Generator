import streamlit as st
from textwrap import wrap

from graph import (
    APPROVAL_WORDS,
    apply_review,
    create_config,
    get_workflow_snapshot,
    resume_workflow,
    run_to_next_interrupt,
)


st.set_page_config(
    page_title="Blog Generator",
    page_icon="✍️",
    layout="wide",
)


def initialize_session_state():
    if "workflow_config" not in st.session_state:
        st.session_state.workflow_config = create_config()
    if "topic" not in st.session_state:
        st.session_state.topic = ""
    if "revision_feedback" not in st.session_state:
        st.session_state.revision_feedback = ""
    if "workflow_started" not in st.session_state:
        st.session_state.workflow_started = False


def start_workflow(topic: str):
    st.session_state.workflow_config = create_config()
    st.session_state.topic = topic.strip()
    st.session_state.revision_feedback = ""
    st.session_state.workflow_started = True

    initial_state = {
        "topic": st.session_state.topic,
        "human_feedback": "",
        "is_approved": False,
    }
    run_to_next_interrupt(initial_state, st.session_state.workflow_config)


def current_snapshot():
    if not st.session_state.workflow_started:
        return None
    return get_workflow_snapshot(st.session_state.workflow_config)


def workflow_complete(snapshot) -> bool:
    return snapshot is not None and not snapshot.next


def workflow_progress(snapshot) -> tuple[int, str]:
    if snapshot is None:
        return 0, "Not started"
    if not snapshot.next:
        return 100, "Completed"

    stage = snapshot.values.get("current_stage", "")
    if stage == "research":
        return 33, "Researching"
    if stage == "writing":
        return 66, "Writing"
    if stage == "editing":
        return 85, "Editing"
    return 95, "Ready for review"


def build_pdf_bytes(title: str, article: str) -> bytes:
    def escape_pdf_text(value: str) -> str:
        return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    lines = [title, ""]
    for paragraph in article.splitlines() or [article]:
        wrapped = wrap(paragraph, width=90) or [""]
        lines.extend(wrapped)
        lines.append("")

    content_lines = ["BT", "/F1 12 Tf", "72 760 Td", "14 TL"]
    for line in lines:
        content_lines.append(f"({escape_pdf_text(line)}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", errors="ignore")

    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj")
    objects.append(b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>endobj")
    objects.append(b"4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj")
    objects.append(f"5 0 obj<< /Length {len(content)} >>stream\n".encode("latin-1") + content + b"\nendstream endobj")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj + b"\n")

    xref_position = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF".encode(
            "latin-1"
        )
    )
    return bytes(pdf)


initialize_session_state()

st.markdown("# Blog Generator")
st.caption("Generate a draft, review the editor feedback, then approve or send it back for revision.")

with st.sidebar:
    st.header("Workflow")
    topic = st.text_input("Blog topic", value=st.session_state.topic, placeholder="Example: How AI is changing local business marketing")
    if st.button("Start workflow", use_container_width=True):
        if not topic.strip():
            st.error("Enter a topic before starting the workflow.")
        else:
            start_workflow(topic)
            st.rerun()

    if st.button("Reset session", use_container_width=True):
        st.session_state.workflow_config = create_config()
        st.session_state.topic = ""
        st.session_state.revision_feedback = ""
        st.session_state.workflow_started = False
        st.rerun()

    st.markdown("---")
    progress_value, progress_label = workflow_progress(current_snapshot())
    st.metric("Status", progress_label)
    st.progress(progress_value / 100)
    st.caption(f"{progress_value}% complete")

    if st.session_state.workflow_started:
        snapshot = current_snapshot()
        if snapshot and snapshot.values.get("article"):
            pdf_bytes = build_pdf_bytes(
                f"Blog Draft - {st.session_state.topic}",
                snapshot.values.get("article", ""),
            )
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"blog_draft_{st.session_state.topic.lower().replace(' ', '_') or 'draft'}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


snapshot = current_snapshot()

if not st.session_state.workflow_started:
    st.info("Start the workflow from the sidebar to generate a draft.")
else:
    st.subheader(f"Topic: {st.session_state.topic}")

    if snapshot is None:
        st.warning("No workflow state is available yet.")
    elif workflow_complete(snapshot):
        st.success("Workflow completed successfully.")
        st.markdown("## Final approved blog post")
        st.markdown(snapshot.values.get("article", ""))

        final_pdf = build_pdf_bytes(
            f"Final Blog Post - {st.session_state.topic}",
            snapshot.values.get("article", ""),
        )
        st.download_button(
            "Download final PDF",
            data=final_pdf,
            file_name=f"final_blog_{st.session_state.topic.lower().replace(' ', '_') or 'post'}.pdf",
            mime="application/pdf",
        )
    else:
        state = snapshot.values
        st.markdown("### Draft")
        st.markdown(state.get("article", "Draft will appear here after the writer finishes."))

        st.markdown("### Editor critique")
        st.markdown(state.get("editor_feedback", "Feedback will appear here after the editor finishes."))

        st.markdown("### Review")
        st.write("Approve the draft or send it back with revision notes.")
        revision_feedback = st.text_area(
            "Revision instructions",
            value=st.session_state.revision_feedback,
            placeholder="What should the research and writing team change?",
            height=140,
        )

        action_left, action_right = st.columns(2)
        with action_left:
            if st.button("Approve draft", use_container_width=True):
                apply_review(st.session_state.workflow_config, True, "")
                resume_workflow(st.session_state.workflow_config)
                st.rerun()

        with action_right:
            if st.button("Send back for revision", use_container_width=True):
                if not revision_feedback.strip():
                    st.error("Add revision instructions before sending the draft back.")
                else:
                    st.session_state.revision_feedback = revision_feedback.strip()
                    apply_review(st.session_state.workflow_config, False, st.session_state.revision_feedback)
                    resume_workflow(st.session_state.workflow_config)
                    st.rerun()

        if state.get("current_stage"):
            st.caption(f"Current stage: {state.get('current_stage')}")
        if state.get("human_feedback"):
            st.caption(f"Saved feedback: {state.get('human_feedback')}")

st.sidebar.markdown("---")
st.sidebar.caption(f"Approval words supported by the workflow: {', '.join(sorted(APPROVAL_WORDS))}")