"""Database settings section for settings page."""

import streamlit as st
import os

from finarius_app.core.database import get_db_path, backup_db, restore_db, vacuum_db, get_db_stats
from finarius_app.ui.session_state import get_db, set_success_message, set_error_message


def render_database_settings(db) -> None:
    """Render database settings section.
    
    Args:
        db: Database instance.
    """
    st.subheader("💾 Database Settings")
    
    try:
        # Display database path
        db_path = get_db_path(db)
        st.text_input("Database Path", value=db_path, disabled=True, help="Current database file path")
        
        # Database statistics
        stats = get_db_stats(db)
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                if "file_size_mb" in stats:
                    st.metric("Database Size", f"{stats['file_size_mb']:.2f} MB")
            with col2:
                if "table_counts" in stats:
                    total_rows = sum(stats["table_counts"].values())
                    st.metric("Total Records", f"{total_rows:,}")
            with col3:
                if "schema_version" in stats:
                    st.metric("Schema Version", stats["schema_version"])
        
        st.markdown("---")
        
        # Backup database
        st.markdown("#### Backup Database")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("Create a backup of the current database. The backup will be saved with a timestamp.")
        with col2:
            if st.button("📦 Backup", use_container_width=True):
                try:
                    backup_path = backup_db(db)
                    set_success_message(f"Database backed up successfully to: {backup_path}")
                    st.rerun()
                except Exception as e:
                    set_error_message(f"Error backing up database: {str(e)}")
                    st.rerun()
        
        # Restore database
        st.markdown("#### Restore Database")
        st.warning("⚠️ Restoring a database will replace the current database. This action cannot be undone!")
        
        uploaded_file = st.file_uploader("Choose backup file to restore", type=["sqlite", "db", "backup"])
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"Ready to restore from: {uploaded_file.name}")
            with col2:
                if st.button("🔄 Restore", use_container_width=True, type="primary"):
                    try:
                        restore_db(tmp_path)
                        set_success_message("Database restored successfully! Please refresh the page.")
                        os.unlink(tmp_path)  # Clean up temp file
                        st.rerun()
                    except Exception as e:
                        set_error_message(f"Error restoring database: {str(e)}")
                        os.unlink(tmp_path)  # Clean up temp file
                        st.rerun()
        
        # Vacuum database
        st.markdown("---")
        st.markdown("#### Optimize Database")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("Vacuum the database to reclaim unused space and optimize performance.")
        with col2:
            if st.button("🧹 Vacuum", use_container_width=True):
                try:
                    vacuum_db(db)
                    set_success_message("Database vacuum completed successfully!")
                    st.rerun()
                except Exception as e:
                    set_error_message(f"Error vacuuming database: {str(e)}")
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error loading database settings: {str(e)}")

