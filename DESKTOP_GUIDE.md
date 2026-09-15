# Questionnaire Review for Windows

## Install and open

Run `QuestionnaireReview-Setup-1.0.0.exe`. The installer installs for your Windows account, creates a Start Menu shortcut and offers an optional desktop shortcut. Open **Questionnaire Review**. Your browser opens when the app is ready. Python and terminal commands are not needed.

For the portable edition, extract the entire zip and double-click `QuestionnaireReview.exe`. Keep its `_internal` folder beside the executable. A Windows x64 computer and internet connection for Google are required.

## First use

In the browser sidebar, open **Google settings**, enter the API key and generation model supplied by your administrator, then select **Save settings**. **Test Google connection** checks access to model metadata; generation/embedding quota is checked when those requests run. The key is stored in Windows Credential Manager for your account. Existing environment variables override saved settings.

Upload a questionnaire CSV. The bundled sample questionnaires are in `_internal/questionnaires` in the portable/installation directory. Select **Generate draft**, inspect evidence, review routed or failed rows, then download the CSV and workbook. Google receives questions and evidence for processing. The supplied case-study data is synthetic.

## Close and reopen

Closing the browser tab leaves the app running. Find the Q icon near the Windows clock (it may be inside the hidden-icons arrow). Right-click it and select **Open application** to reopen the browser, or **Exit** to stop the app. Wait for current generation to finish before exiting. Completed rows remain saved; interrupted work may need retry. Opening the shortcut again while the app is running reopens the existing session.

## Your files

Jobs, embedding cache and startup log are under `%LOCALAPPDATA%\QuestionnaireReview`. Installation upgrades do not replace that folder. Uninstall removes application files and shortcuts but retains your jobs/cache and saved credentials. Use **Remove saved settings** in the app before uninstalling if you want to remove the saved key/model. Source-web-app databases are not automatically imported.

If the browser does not open, use the tray's **Open application** option. If startup fails, the error points to `desktop-server.log` in the data folder. Share logs only with your administrator after checking them for sensitive content. Google account/model/quota errors still require the appropriate account configuration.

The installer and executable are unsigned. Windows may warn about an unknown publisher. Use only the package and SHA-256 checksum supplied by your trusted sender. This local demo has not been tested on a separate Windows VM without Python; see the desktop verification report for the checks actually run.
