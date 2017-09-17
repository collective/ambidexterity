/*globals jQuery, alert */

if(require === undefined){
  // plone 4
  require = function(reqs, torun){
    'use strict';
    return torun(window.jQuery);
  };
}

if (window.jQuery && define) {
  define( 'jquery', [], function () {
    'use strict';
    return window.jQuery;
  } );
}

require([
  'jquery',
  'ace'
], function($) {
  'use strict';

    var inventory = null,
        content_type_select = $("#content_types"),
        fields_select = $("#cfields"),
        save_form = $("#saveform"),
        field_scripts = ['default', 'validator', 'vocabulary'],
        script_operators = ['add', 'edit', 'remove'],
        editor,
        doc_changed;

    function get_authenticator() {
        return $('input[name="_authenticator"]').val();
    }

    function fill_fields(selected) {
        fields_select.empty();
        $.each(inventory[selected].fields, function(key, val) {
            fields_select.append(
                $("<option />", {
                    value: key,
                    html: val.title
                })
            );
        });
        fields_select.change();
    }

    function fill_content_select() {
        var selected = content_type_select.val();

        content_type_select.empty();
        $.each(inventory, function(key, val) {
            var new_option;

            new_option = $("<option />", {
                value: key,
                html: val.title
            });
            content_type_select.append(new_option);
        });
        if (!selected) {
            selected = content_type_select.children().eq(0).val();
        }
        content_type_select.val(selected);
        fill_fields(selected);
    }

    function get_inventory() {
        $.getJSON("@@ambidexterityajax/resource_inventory?_authenticator=" + get_authenticator(), function(data) {
            inventory = data;
            fill_content_select();
        });
    }

    content_type_select.change(function () {
        fill_fields(content_type_select.val());
    });

    fields_select.change(function () {
        var content_type = content_type_select.val(),
            field_name = fields_select.val(),
            field_info = inventory[content_type].fields[field_name];

        if (field_name) {
            $.each(field_scripts, function(index, value) {
                if (field_info['has_' + value]) {
                    $('#add_' + value).hide();
                    $('#edit_' + value).show();
                    $('#remove_' + value).show();
                } else {
                    $('#add_' + value).show();
                    $('#edit_' + value).hide();
                    $('#remove_' + value).hide();
                }
            });
        } else {
            $.each(field_scripts, function(index, value) {
                $('#add_' + value).hide();
                $('#edit_' + value).hide();
                $('#remove_' + value).hide();
            });
        }
    });

    $("form#available_actions button").click(function (e) {
        var button_id = $(this).attr('id'),
            content_type = content_type_select.val(),
            field_name = fields_select.val(),
            data_in;

        data_in = {
            "button_id": button_id,
            "content_type": content_type,
            "field_name": field_name
        };

        $.post("@@ambidexterityajax/button_action?_authenticator=" + get_authenticator(), data_in, function(data) {
            editor.setValue('');
            if (data.action === 'edit') {
                editor_set_source(data.source);
                save_form.children("input[name='content_type']").val(content_type);
                save_form.children("input[name='field_name']").val(field_name);
                save_form.children("input[name='script']").val(button_id);
            }
            get_inventory();
        }, 'json');
    });


    save_form.submit(function (e) {
        e.preventDefault();

        // TODO: save me!
        enable_actions();
        doc_changed = false;
        $('#save_form :submit').attr('disabled', 'disabled');
    });


    function editor_init() {
        if (!editor) {
            var editor_session;

            if (!window.ace){
                // XXX hack...
                // wait, try loading later
                setTimeout(function() {
                  editor_init();
                }, 200);
                return;
            }
            editor = ace.edit("source_editor");
            // editor.setTheme("ace/theme/monokai");
            editor.setHighlightActiveLine(false);
            editor_session = editor.getSession();
            // editor_session.setMode("ace/mode/python");
            editor_session.setTabSize(4);
            editor_session.setUseSoftTabs(true);
            editor_session.setUseWrapMode(true);

            // Make save keystroke trigger save-form submit
            editor.commands.addCommand({
                name: "save",
                bindKey: {win: "Ctrl-S", mac: "Command-S"},
                exec: function() {
                    save_form.submit();
                }
            });

            // enable save submit button on change
            editor_session.on('change', function(e) {
                $('#saveform :submit').removeAttr('disabled');
                disable_actions();
                doc_changed = true;
            });
        }
    }


    function disable_actions() {
        $("#available_actions :input").attr('disabled', 'disabled');
    }


    function enable_actions() {
        $("#available_actions :input").removeAttr('disabled');
    }


    function editor_set_source(source) {
        var editor_session = editor.getSession();

        editor_session.setValue(source);
        editor.gotoLine(1, 1);
        if (source.endsWith('.pt')) {
            editor_session.setMode("ace/mode/html");
        } else {
            editor_session.setMode("ace/mode/python");
        }
//        editor_session.getUndoManager().reset();
        doc_changed = false;
        $('#saveform :submit').attr('disabled', 'disabled');
    }


    function setEditorSize () {
      var wheight = $(window).height();
      $("#source_editor").height(wheight-80);
    }

    setEditorSize();
    editor_init();

    get_inventory();

});
