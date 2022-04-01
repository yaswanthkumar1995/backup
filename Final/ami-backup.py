# script will search for all instances having a tag with "backup" or "ami" on it
# Replace your Region to take ami
# Replace your Retention value 
import boto3
import collections
import datetime

ec = boto3.client('ec2','ap-south-1') #mention your region to backup

def lambda_handler(event, context):
    
    reservations = ec.describe_instances(
        Filters=[
            {'Name': 'tag-key', 'Values': ['Backup']},
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print("Found %d instances that need backing up" % len(instances))

    to_tag = collections.defaultdict(list)

    for instance in instances:
        
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'Retention'][0]
            
        except IndexError:
            retention_days = 0 #mention Retention day
            
            create_time = datetime.datetime.now()
            create_fmt = create_time.strftime('%d-%m-%Y')
            create_tm = create_time.strftime('%H.%M.%S')
        for name in instance['Tags']:
            Instancename= name['Value']
            key_fil= name['Key']
            if key_fil == 'Name' :
                AMIid = ec.create_image(InstanceId=instance['InstanceId'], Name="Lambda - " + instance['InstanceId'] + "  ("+ Instancename + ")   at " +create_tm+ "  From " + create_fmt, Description="Lambda created AMI of instance " + instance['InstanceId'], NoReboot=True, DryRun=False)
                to_tag[retention_days].append(AMIid['ImageId'])


                print("Retaining AMI %s of instance %s for %d days" % (
                    AMIid['ImageId'],
                    instance['InstanceId'],
                    retention_days,
                    ))

    for retention_days in to_tag.keys():
        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
        delete_fmt = delete_date.strftime('%d-%m-%Y')
        print("Will delete %d AMIs on %s" % (len(to_tag[retention_days]), delete_fmt))
        ec.create_tags(
            Resources=to_tag[retention_days],
            Tags=[
                {'Key': 'DeleteOn', 'Value': delete_fmt},
                {'Key': 'Name', 'Value': instance['InstanceId']},
            ]
        )
