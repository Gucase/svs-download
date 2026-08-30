/* SVS transfers authored SVG using Illustrator's importer, never pixel tracing.
   The Windows entry point supplies SVS_DOCUMENT_JOB after local validation. */
(function (job) {
    var incoming = null, added = null, destination = null, resultDoc = null;
    var importComplete = false, paths = 0, texts = 0, gradients = 0;
    function requireCondition(condition, message) {
        if (!condition) { throw new Error(message); }
    }
    function exportNewFiles(doc) {
        var problem = [];
        if (job.outputAi) {
            try {
                requireCondition(!new File(job.outputAi).exists, 'AI output already exists');
                var aiOptions = new IllustratorSaveOptions();
                aiOptions.pdfCompatible = true;
                doc.saveAs(new File(job.outputAi), aiOptions);
            } catch (aiError) { problem.push('AI: ' + aiError.message); }
        }
        if (job.outputPng) {
            try {
                requireCondition(!new File(job.outputPng).exists, 'PNG output already exists');
                var pngOptions = new ExportOptionsPNG24();
                pngOptions.artBoardClipping = true;
                pngOptions.transparency = true;
                doc.exportFile(new File(job.outputPng), ExportType.PNG24, pngOptions);
            } catch (pngError) { problem.push('PNG: ' + pngError.message); }
        }
        return problem.join('; ');
    }
    try {
        requireCondition(app.documents.length > 0, 'An existing document is required');
        destination = app.activeDocument;
        requireCondition(job.mode === 'append' || job.mode === 'review', 'Invalid mode');
        if (job.mode === 'append') {
            requireCondition(!destination.activeLayer.locked && destination.activeLayer.visible, 'Unlock/show the target layer first');
        }
        // Modal importer notices can deadlock an out-of-process COM caller.
        // Restore the setting immediately, then audit actual imported objects.
        var interactionBeforeImport = app.userInteractionLevel;
        try {
            app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
            incoming = app.open(new File(job.source), DocumentColorSpace.RGB);
        } finally { app.userInteractionLevel = interactionBeforeImport; }
        requireCondition(incoming !== destination, 'Import must use a separate temporary document');
        requireCondition(incoming.rasterItems.length === 0 && incoming.placedItems.length === 0, 'Import contains raster or linked objects');
        paths = incoming.pathItems.length;
        texts = incoming.textFrames.length;
        gradients = incoming.gradients.length;
        requireCondition(paths > 0, 'No native vector paths imported');
        requireCondition(texts >= job.expectedText, 'Live labels were lost during import');
        if (job.mode === 'review') {
            resultDoc = incoming;
        } else {
            var frame = incoming.artboards[0].artboardRect;
            var target = destination.artboards[destination.artboards.getActiveArtboardIndex()].artboardRect;
            var sourceWidth = frame[2] - frame[0], sourceHeight = frame[1] - frame[3];
            requireCondition(sourceWidth > 0 && sourceHeight > 0, 'Invalid source artboard');
            var roots = [], n;
            for (n = 0; n < incoming.pageItems.length; n++) {
                var item = incoming.pageItems[n];
                if (item.parent.typename === 'Layer') { roots.push(item); }
            }
            requireCondition(roots.length > 0, 'No transferable root objects');
            added = destination.activeLayer.groupItems.add();
            added.name = job.groupName;
            for (n = roots.length - 1; n >= 0; n--) { roots[n].duplicate(added, ElementPlacement.PLACEATBEGINNING); }
            var factor = Math.min((target[2] - target[0]) * job.widthFraction / sourceWidth,
                                  (target[1] - target[3]) * job.heightFraction / sourceHeight);
            var left = target[0] + ((target[2] - target[0]) - sourceWidth * factor) / 2;
            var top = target[1] - ((target[1] - target[3]) - sourceHeight * factor) / 2;
            if (job.placement.indexOf('left') >= 0) { left = target[0]; }
            if (job.placement.indexOf('right') >= 0) { left = target[2] - sourceWidth * factor; }
            if (job.placement.indexOf('top') >= 0) { top = target[1]; }
            if (job.placement.indexOf('bottom') >= 0) { top = target[3] + sourceHeight * factor; }
            var mapping = app.getIdentityMatrix();
            mapping.mValueA = factor; mapping.mValueD = factor;
            mapping.mValueTX = left - frame[0] * factor;
            mapping.mValueTY = top - frame[1] * factor;
            added.transform(mapping, true, true, true, true, factor * 100, Transformation.DOCUMENTORIGIN);
            requireCondition(added.pageItems.length > 0, 'Transfer produced an empty group');
            resultDoc = destination;
            incoming.close(SaveOptions.DONOTSAVECHANGES);
            incoming = null; // Only this job's transient document was closed.
        }
        importComplete = true;
        var exportIssue = exportNewFiles(resultDoc);
        return 'SVS_IMPORT_OK|' + encodeURIComponent(resultDoc.name) + '|' + paths + '|' + texts + '|' + gradients + '|' + encodeURIComponent(exportIssue);
    } catch (failure) {
        if (!importComplete) {
            if (added !== null) { try { added.remove(); } catch (ignoredGroup) {} }
            if (incoming !== null && incoming !== destination) { try { incoming.close(SaveOptions.DONOTSAVECHANGES); } catch (ignoredDoc) {} }
        }
        return 'SVS_IMPORT_FAILED|' + encodeURIComponent(failure.message);
    }
})(SVS_DOCUMENT_JOB);
