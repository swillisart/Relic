from PySide2.QtCore import ( 
    QFile
)

def openResource(resource_path):
    resource_file = QFile(resource_path)
    if resource_file.open(QFile.ReadOnly):
        result = resource_file.readAll()
    return result
