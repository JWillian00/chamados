
toastr.options = {
    "closeButton": true,
    "debug": false,
    "newestOnTop": true,
    "progressBar": true,
    "positionClass": "toast-top-right",  
    "preventDuplicates": true,
    "showDuration": "300",
    "hideDuration": "1000",
    "timeOut": "5000",  // duração visível (ms)
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
};

const notificationSystem = {
    success: function(message, title = 'Sucesso!') {
        toastr.success(message, title);
    },
    error: function(message, title = 'Erro!') {
        toastr.error(message, title);
    },
    info: function(message, title = 'Informação!') { 
        toastr.info(message, title);
    },
    warning: function(message, title = 'Atenção!') { 
        toastr.warning(message, title);
    }
};

window.notificationSystem = notificationSystem;