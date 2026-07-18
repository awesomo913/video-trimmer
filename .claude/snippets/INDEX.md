# Snippet Library

## Utilities

- [`_setup_dnd`](utilities/_setup_dnd.py) (from `app.py:126`) -- Enable drag-and-drop via tkinterdnd2 if available, otherwise skip.
- [`_on_frame_update`](utilities/_on_frame_update.py) (from `app.py:215`) -- Called ~30fps during playback to update the timeline playhead.
- [`_on_trim_change`](utilities/_on_trim_change.py) (from `app.py:235`) -- Called when trim handles are dragged or timecodes are entered.
- [`scan_folder`](utilities/scan_folder.py) (from `services/batch_split_service.py:87`) -- Find every video in `path`, probe metadata, return sorted entries.
- [`compute_segments`](utilities/compute_segments.py) (from `services/batch_split_service.py:130`) -- Return (start, end) pairs in seconds. Empty list = skip this file.
- [`build_output_path`](utilities/build_output_path.py) (from `services/batch_split_service.py:164`) -- `<basename>_part_<n>_of_<N>.<ext>`, zero-padded to width if N >= 10.
- [`crop_box_pixels`](utilities/crop_box_pixels.py) (from `services/edit_transforms.py:14`) -- Return (x, y, w, h) in source pixel coords, or None if crop disabled.
- [`apply_pil_transforms`](utilities/apply_pil_transforms.py) (from `services/edit_transforms.py:33`) -- Apply crop / rotation / flip for preview and snapshot export.
- [`ffmpeg_vf_chain`](utilities/ffmpeg_vf_chain.py) (from `services/edit_transforms.py:56`) -- Build -vf filter string, or None when no video transforms.
- [`get_metadata`](utilities/get_metadata.py) (from `services/ffmpeg_service.py:66`) -- Run ffprobe and return structured metadata.
- [`build_trim_cmd`](utilities/build_trim_cmd.py) (from `services/ffmpeg_service.py:129`) -- Build the ffmpeg command list for a trim job.
- [`open_video`](utilities/open_video.py) (from `services/video_service.py:67`) -- Open a video file and return populated VideoState.
- [`read_frame_at`](utilities/read_frame_at.py) (from `services/video_service.py:87`) -- Seek to a specific frame and return it as a PIL Image.
- [`read_frame_at_time`](utilities/read_frame_at_time.py) (from `services/video_service.py:100`) -- Seek to a specific time and return the frame.
- [`generate_thumbnails`](utilities/generate_thumbnails.py) (from `services/video_service.py:106`) -- Generate evenly-spaced thumbnail images in a background thread.
- [`_start_audio`](utilities/_start_audio.py) (from `services/video_service.py:184`) -- Spawn ffplay -nodisp -autoexit at current video position.
- [`seek_frame`](utilities/seek_frame.py) (from `services/video_service.py:238`) -- Seek to a specific frame (works while paused or playing).
- [`step`](utilities/step.py) (from `services/video_service.py:256`) -- Step forward/back by delta frames.
- [`update_from`](utilities/update_from.py) (from `widgets/batch_file_row.py:84`) -- Re-render after status/progress change.
- [`_refresh_mode_state`](utilities/_refresh_mode_state.py) (from `widgets/split_config_panel.py:165`) -- Visually grey out the inactive group.
- [`set_enabled`](utilities/set_enabled.py) (from `widgets/split_config_panel.py:226`) -- Lock the whole panel during a running batch.
- [`attach_state`](utilities/attach_state.py) (from `widgets/timeline.py:57`) -- Load a new video — regenerate thumbnails and reset handles.
- [`_draw_overlays`](utilities/_draw_overlays.py) (from `widgets/timeline.py:97`) -- Draw trim region, handles, and playhead.
- [`_draw_trim_region`](utilities/_draw_trim_region.py) (from `widgets/timeline.py:115`) -- Draw a semi-transparent overlay on the trimmed region.
- [`_draw_handles`](utilities/_draw_handles.py) (from `widgets/timeline.py:147`) -- Draw the in/out trim handles as colored rectangles with grip lines.
- [`_draw_playhead`](utilities/_draw_playhead.py) (from `widgets/timeline.py:196`) -- Draw the current position indicator as a white vertical line.
- [`update_playhead`](utilities/update_playhead.py) (from `widgets/timeline.py:215`) -- Called by the app to update playhead position during playback.
- [`set_trim`](utilities/set_trim.py) (from `widgets/timeline.py:275`) -- Programmatically set trim points.
- [`update_display`](utilities/update_display.py) (from `widgets/trim_controls.py:154`) -- Refresh the timecode entries and duration from current state.
- [`attach_state`](utilities/widgets__attach_state.py) (from `widgets/video_preview.py:108`) -- Attach a new video state after opening a file.
- [`_show_frame`](utilities/_show_frame.py) (from `widgets/video_preview.py:190`) -- Remember raw pixels, apply edits, scale to the label, and show.
- [`_render_from_raw`](utilities/_render_from_raw.py) (from `widgets/video_preview.py:195`) -- Apply crop/rotate/flip from state, then scale to fit.
- [`refresh_after_edit`](utilities/refresh_after_edit.py) (from `widgets/video_preview.py:214`) -- Re-render the current frame after crop/rotate/flip changes (paused UI).
- [`get_snapshot_image`](utilities/get_snapshot_image.py) (from `widgets/video_preview.py:220`) -- Current frame with edits applied (safe while playing via last-frame cache).

## Classes

- [`SplitConfig`](classes/SplitConfig.py) (from `services/batch_split_service.py:30`) -- Per-batch configuration: how to split and how to encode.
- [`BatchFileEntry`](classes/BatchFileEntry.py) (from `services/batch_split_service.py:49`) -- One video in the batch — populated by scan, mutated by runner.
- [`BatchSplitJob`](classes/BatchSplitJob.py) (from `services/batch_split_service.py:70`) -- Top-level batch run state.
- [`VideoMeta`](classes/VideoMeta.py) (from `services/ffmpeg_service.py:16`)
- [`TrimJob`](classes/TrimJob.py) (from `services/ffmpeg_service.py:111`) -- Holds state for a running trim operation.
- [`VideoState`](classes/VideoState.py) (from `services/video_service.py:17`) -- Shared mutable state for the currently loaded video.
- [`BatchFileRow`](classes/BatchFileRow.py) (from `widgets/batch_file_row.py:39`) -- One row: filename, duration, status badge, thin progress bar.
- [`ModeSwitcher`](classes/ModeSwitcher.py) (from `widgets/mode_switcher.py:12`) -- Two-button segmented control. Active button gets accent color.
- [`StatusBar`](classes/StatusBar.py) (from `widgets/status_bar.py:10`) -- Bottom bar with left status text and right-aligned file info.
- [`Toast`](classes/Toast.py) (from `widgets/toast.py:24`) -- Ephemeral toast that appears top-right and auto-dismisses.
- [`Toolbar`](classes/Toolbar.py) (from `widgets/toolbar.py:12`) -- Horizontal toolbar with branding, buttons, and metadata display.
- [`TrimControls`](classes/TrimControls.py) (from `widgets/trim_controls.py:14`) -- Horizontal bar with in/out timecodes, set buttons, and trim duration.

## Patterns

- [`__init__`](patterns/__init__.py) (from `app.py:32`)
- [`_build_ui`](patterns/_build_ui.py) (from `app.py:62`)
- [`_load_video`](patterns/_load_video.py) (from `app.py:152`)
- [`format_time`](patterns/format_time.py) (from `services/ffmpeg_service.py:45`)
- [`parse_time`](patterns/parse_time.py) (from `services/ffmpeg_service.py:56`)
- [`loaded`](patterns/loaded.py) (from `services/video_service.py:49`)
- [`__init__`](patterns/services____init__.py) (from `services/video_service.py:153`)
- [`__init__`](patterns/widgets____init__.py) (from `widgets/batch_file_row.py:42`)
- [`__init__`](patterns/widgets____init___2.py) (from `widgets/batch_panel.py:40`)
- [`__init__`](patterns/widgets____init___3.py) (from `widgets/export_dialog.py:23`)
- [`__init__`](patterns/widgets____init___4.py) (from `widgets/mode_switcher.py:15`)
- [`__init__`](patterns/widgets____init___5.py) (from `widgets/split_config_panel.py:19`)
- [`__init__`](patterns/widgets____init___6.py) (from `widgets/status_bar.py:13`)
- [`__init__`](patterns/widgets____init___7.py) (from `widgets/timeline.py:21`)
- [`__init__`](patterns/widgets____init___8.py) (from `widgets/toast.py:29`)
